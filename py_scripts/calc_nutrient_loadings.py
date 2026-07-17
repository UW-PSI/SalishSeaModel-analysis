#!/usr/bin/env python3
# Created by Ben Roberts at the Puget Sound Institute with funding from
# King County.
# Some code by Rachael D. Mueller adapted and reused. Intended as a
# replacement for the notebook Table1_NutrientLoadings.ipynb

# Computes DIN loading by default (NH4 + NO3). To compute TN, run with
# the option "--variables nh4 no3 ldon rdon lpon rpon --" (the final --
# is needed so the argument processor know it's reached the end of all
# the options)

import logging
from datetime import date
from argparse import ArgumentParser
from pathlib import Path
import pandas as pd
import numpy as np

import ssm_utils
import ssm_read_fwinputs

def _mega_merge(dfs, startdf):
    """Merge a bunch of dataframes together.

    Second argument is a dataframe to start with.
    """
    merged = startdf
    for df in dfs:
        merged = merged.merge(df, left_index=True, right_index=True)
    return merged

def calc_nutrient_loadings(inputs: dict, variables: list,
                           altered_only=False):
    riv_dfs = []
    wwtp_dfs = []
    riv_names = {}
    wwtp_names = {}
    for rt, fn in inputs.items():
        with open(fn) as fp:
            # Start date doesn't matter
            inputdata, *_ = ssm_read_fwinputs.read_dat_file(fp, '2014.01.01')

        # Filter out the first day of the following year if present
        data_1year = inputdata['data'].loc[inputdata['data'].index.get_level_values(0).year == inputdata['data'].index.levels[0].year[0]]
        # To reproduce the Whidbey report values exactly, comment out the
        # above line and uncomment the one below.
        #data_1year = inputdata['data']

        total_flow_m3yr = data_1year.groupby(level=(2))['discharge'].sum() * 24 * 3600

        # Group all sources by FVCOM ID
        riv_ids = []
        riv_nodes = []
        riv_regions = []
        riv_loads = []
        wwtp_ids = []
        wwtp_nodes = []
        wwtp_regions = []
        wwtp_loads = []
        for fvcomid, group in inputdata['nodes'].groupby(level=1):
            # aggregate the loading data
            data = data_1year.xs(fvcomid, level=2)
            loading = ((data['discharge'] * data[variables].sum(axis='columns')
                        ) * 86.4).sum()
            if group['Source Type'].iloc[0] == 'River':
                riv_ids.append(fvcomid)
                riv_nodes.append(','.join([str(i) for i in group.index.get_level_values(0)]))
                riv_regions.append(group['Region'].iloc[0])
                riv_names[fvcomid] = group['Name'].iloc[0]
                riv_loads.append(loading)
            else:
                wwtp_ids.append(fvcomid)
                wwtp_nodes.append(group.index[0][0])
                wwtp_regions.append(group['Region'].iloc[0])
                wwtp_names[fvcomid] = group['Name'].iloc[0]
                wwtp_loads.append(loading)
        riv_dfs.append(pd.DataFrame({rt: riv_loads}, index=riv_ids))
        wwtp_dfs.append(pd.DataFrame({rt: wwtp_loads}, index=wwtp_ids))
    # Now join all the river DFs together
    rivers = pd.DataFrame({
        'Name': riv_names,
        'Node': riv_nodes,
        'Region': riv_regions,
        'Annual Total Flow (m^3/year)': total_flow_m3yr.loc[riv_ids],
        'Annual Total Flow (MGal/year)': total_flow_m3yr.loc[riv_ids] * 0.0002642
    }, index=riv_ids)
    rivers = _mega_merge(riv_dfs, rivers).set_index('Name')
    wwtps = pd.DataFrame({
        'Name': wwtp_names,
        'Node': wwtp_nodes,
        'Region': wwtp_regions,
        'Annual Total Flow (m^3/year)': total_flow_m3yr.loc[wwtp_ids],
        'Annual Total Flow (MGal/year)': total_flow_m3yr.loc[wwtp_ids] * 0.0002642
    }, index=wwtp_ids)
    metacol_ct = len(wwtps.columns) - 1 # Name becomes the index so don't count it
    wwtps = _mega_merge(wwtp_dfs, wwtps).set_index('Name')
    riv_totals = rivers.sum(axis=0)
    wwtp_totals = wwtps.sum(axis=0)
    # This summed a few things for which sums don't make sense, so empty those cells
    metacols = ['Node','Region']
    for c in metacols:
        riv_totals[c] = np.nan
        wwtp_totals[c] = np.nan
    # Now consider all the columns with loading info in them to see
    # if they are the same across runs, and filter those matches out
    if altered_only:
        # From https://stackoverflow.com/a/22701944
        loading_cols = rivers[rivers.columns[metacol_ct:]]
        rivers = rivers.loc[~loading_cols.eq(loading_cols.iloc[:, 0], axis=0).all(axis=1)]
        loading_cols = wwtps[wwtps.columns[metacol_ct:]]
        wwtps = wwtps.loc[~loading_cols.eq(loading_cols.iloc[:, 0], axis=0).all(axis=1)]
        print(f'Number of WWTPs in this case: {len(wwtps)}')
        print(f'Number of rivers in this case: {len(rivers)}')
    print(f'Number of WWTPs in model: {len(wwtp_ids)}')
    print(f'Number of rivers in model: {len(riv_ids)}')
    return rivers, wwtps, riv_totals, wwtp_totals

def main():
    parser = ArgumentParser(description='Compute nutrient loadings from a freshwater boundary condition')

    parser.add_argument('case', help='Case name or path to a YAML file')
    parser.add_argument('excel_output_path', type=Path, nargs='?', default=Path('.'),
                        help='Optional path and filename for output')
    parser.add_argument('--variables', nargs='*',
                        default=['nh4','no32'],
                        help='Variables to consider as nutrients. DIN by default')
    parser.add_argument('--altered-only', action='store_true',
                        help='Restrict output to loadings that vary across scenarios')

    args = parser.parse_args()

    ssm, case = ssm_utils.read_case(args.case)

    rivers, wwtps, rivtotals, wwtptotals = calc_nutrient_loadings(
            ssm['paths']['nutrient_loading_inputs'], args.variables,
            altered_only=args.altered_only)
    riv_footer = [pd.DataFrame(rivtotals.to_dict(), index=['Total Rivers (all in model domain)'])]
    wwtp_footer = [pd.DataFrame(wwtptotals.to_dict(), index=['Total WWTPs (all in model domain)'])]
    if args.altered_only:
        riv_totals = rivers.sum(axis=0).to_dict()
        wwtp_totals = wwtps.sum(axis=0).to_dict()
        # This summed a few things for which sums don't make sense, so
        # empty those cells
        metacols = ['Node','Region']
        for c in metacols:
            del riv_totals[c]
            del wwtp_totals[c]
        riv_footer.insert(0, pd.DataFrame(riv_totals, index=['Total Rivers (altered in this report)']))
        wwtp_footer.insert(0, pd.DataFrame(wwtp_totals, index=['Total WWTPs (altered in this report)']))
    rivers = pd.concat([rivers] + riv_footer)
    wwtps = pd.concat([wwtps] + wwtp_footer)

    # make README
    this_file = '=HYPERLINK("https://github.com/UW-PSI/SalishSeaModel-analysis/blob/main/py_scripts/calc_nutrient_loadings.py")'
    run_description = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/docs/supporting/KingCounty_Model_Runs.xlsx","KingCounty_Model_Runs.xlsx (USING ORIGINAL RUN TAGS!!!)")'

    created_by = 'Ben Roberts'
    created_at = 'Puget Sound Institute'
    created_from = 'Model results produced by Su Kyong Yun (PNNL) and Rachael Mueller (PSI)'
    units='kg/year'
    variables=','.join(args.variables)
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_at, created_on, this_file,
            variables, units, created_from,
            run_description]
    }
    header_df = pd.DataFrame(header, index=[
        'Created by',
        'Created at',
        'Created on',
        'Created with',
        'Variables summed',
        'Loading units',
        'Modeling by',
        'Model Run Overview'])

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Save output to excel
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    output_path = args.excel_output_path / f'Table1_NutrientLoadings_{case}.xlsx' if args.excel_output_path.is_dir() else args.excel_output_path
    print('*************************************************************')
    print('Writing spreadsheet to: ', output_path)
    print('*************************************************************')
    if not output_path.parent.is_dir():
        print(f'creating: {output_path.parent}')
        os.umask(0) #clears permissions
        os.makedirs(output_path.parent, mode=0o777,exist_ok=True)
    with pd.ExcelWriter(output_path, mode='w') as writer:  
        wwtps.to_excel(writer, sheet_name=f'WWTP ({case})')
        rivers.to_excel(writer, sheet_name=f'Rivers ({case})')
        header_df.to_excel(writer, sheet_name='README')

if __name__ == "__main__": main()
