#!/usr/bin/env python3
# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
import argparse
import os
from pathlib import Path
import time
from datetime import date

import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd

# load functions from my scripts file "ssm_utils"
from ssm_utils import read_case, VolAreaStats, DOCompliance

def calc_noncompliant_TS(shp, case, noncompliance, model_var, run_type,
                         human_allowance=-0.2, include_parta=True):
    """
    HEADER TO BE ADDED
    This script requires inclusion of reference case subdirectory in 
    ssm['paths']['processed_output'] as well as a specification of the reference
    case sub-directory name in the yaml file under: ssm['run_information']['reference']
    """

    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby(
        'Regions').count().index.to_list()
    regions.remove('Other')
    print(regions)

    # Load minimum DO results from scenario
    processed_netcdf_dir = Path(ssm['paths']['processed_output']) / case
    run_file = processed_netcdf_dir / model_var / run_type / 'wc' / f'daily_min_{model_var}_wc.nc'
    MinDO_full={}
    MinDO={}
    try: 
        with xr.open_dataset(run_file) as ds:
            print([*ds])
            MinDO_full[run_type]=ds[f'{model_var}_daily_min_wc']
            MinDO[run_type] = MinDO_full[run_type]
    except FileNotFoundError:
        print(f'File Not Found: {run_file}')

    # Load minimum DO results from reference case
    # Define reference run
    reference = ssm['run_information']['reference']
    reference_file = processed_netcdf_dir / model_var / reference / 'wc' / f'daily_min_{model_var}_wc.nc'
    with xr.open_dataset(reference_file) as ds:
        MinDO_full[reference]=ds[f'{model_var}_daily_min_wc']
        MinDO[reference]=MinDO_full[reference]

    docomp = DOCompliance(gdf, MinDO[run_type].shape,
                          non_compliant_threshold=noncompliance,
                          human_allowance=human_allowance,
                          include_parta=include_parta)
    stats = VolAreaStats(ssm_config=ssm, gdf=gdf, sizes=MinDO[reference].sizes)

    # Calculate noncompliance
    print(f'Calculating difference for {run_type}')
    DO_diff_lt_0p2 = docomp.find_noncompliant(MinDO[run_type], MinDO[reference])

    VolumeDays = stats.apply(DO_diff_lt_0p2)

    # percent of region's volume that is noncompliant
    total_area_noncompliant_byRegion = {run_type: {}}
    for region in regions: 
        # time series of noncompliant volume in regions for each day
        (total_noncompl_area,
         total_area_noncompliant_byRegion[run_type][region]) = stats.get_area_stats_by_region(region)

    # repeat the above for the entire domain
    (total_noncompl_area,
     total_area_noncompliant_byRegion[run_type]['ALL_REGIONS']) = stats.get_area_stats_by_region('all')

    # Convert to dataframe and organize information
    TotalAreaNoncompliant_df = pd.DataFrame(total_area_noncompliant_byRegion[run_type])
    
    return TotalAreaNoncompliant_df

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    noncompliance: -0.2 in Bounding Scenarios and -0.25 in Optimization
    """
    parser = argparse.ArgumentParser(description='Compute timeseries of noncompliant area')
    parser.add_argument('noncompliance', type=float, help='Compliance threshold. -0.2 in Bounding Scenarios and -0.25 in Optimization')
    parser.add_argument('case', help='Case name')
    parser.add_argument('run_type', help='Short name for the run to analyze')
    parser.add_argument('--model-var', default='DOXG', help='Model state variable to check for compliance')
    parser.add_argument('--no-parta', action='store_true',
                        help='Ignore part A of the water quality standard')
    args = parser.parse_args()

    human_allowance = -0.2

    # backwards compatibility: if a full file path was given as the third argument, get run_type from it
    if os.path.isfile(args.run_type) and args.run_type[-3:] == '.nc':
        args.run_type = args.run_type.split('/')[-3]

    # convert noncompliance to text string to use in file name
    noncompliant_txt = str(args.noncompliance)
    noncompliant_txt = noncompliant_txt.replace('.','p')
    noncompliant_txt = noncompliant_txt.replace('-','m')
    if args.no_parta:
        noncompliant_txt += '_noparta'

    # Start time counter
    start = time.perf_counter()
    
    # Load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config_*.ipynb
    ssm, case = read_case(args.case)
    # get shapefile path
    shp = ssm['paths']['shapefile']

    output_directory = Path(ssm['paths']['spreadsheets']) / 'noncompliance'
    # create output directory, if is doesn't already exist
    if not output_directory.is_dir():
        output_directory.mkdir(parents=True, exist_ok=True)

    TotalAreaNoncompliant_df = calc_noncompliant_TS(
            shp, case, args.noncompliance, args.model_var, args.run_type,
            include_parta=not args.no_parta,
            human_allowance=human_allowance
        )

    # Create a run scenario tag-name for file naming
    if args.run_type.split("_")[0] != 'wqm':
        run_tag = args.run_type.split("_")[0]
    else:
        run_tag = args.run_type

    # make README 
    this_file = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/scripts/calc_DO_noncompliance_timeseries.py","calc_DO_noncompliant_area_timeseries.py")'
    run_description = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/docs/supporting/KingCounty_Model_Runs.xlsx","KingCounty_Model_Runs.xlsx")'
    run_name_on_hyak=f'This run is stored on Hyak under the tag {run_tag}'
    noncompliance_value=f'{args.noncompliance} mg/l'
    noncompliant = f'Non-compliance in this table is defined as < {args.noncompliance} mg/l. An noncompliance threshold of -0.25 is described in pages 49 and 50 of the Optimization report appendix.'
    noncompliant_link = '=HYPERLINK("https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf", "Optimization Report Appendix")'
    HA=f"{human_allowance}: Pre-industrial DO must be less than DO standard plus human allowance to be considered for Part B of the Dept. of Ecology's non-compliance calculation"
    created_by = ssm['author']
    created_at = 'Puget Sound Institute'
    created_from = 'Model results produced by Su Kyong Yun (PNNL) and Rachael D. Mueller (PSI)'
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_at, created_on, this_file,
            created_from,
            run_description, run_name_on_hyak, noncompliance_value, HA, noncompliant,
            noncompliant_link]
    }
    header_df = pd.DataFrame(header, index=[
        'Created by',
        'Created at',
        'Created on',
        'Created with',
        'Modeling by',
        'Model Run Overview',
        'Hyak name',
        'Non-compliant threshold [mg/l]',
        'Human Allowance [mg/l]',
        'Non-compliant Reference',
        'Non-compliant Reference'])

    # Save to file
    # map file name from Hyak run-name to reference run-name
    print(run_tag)
    if run_tag == "wqm_baseline":
        output_file = f"{case}_baseline_wc_noncompliant_AREA_{noncompliant_txt}_TS_byRegion.xlsx"
    else:
        output_file = f"{case}_{ssm['run_information']['run_tag'][case][run_tag]}_wc_noncompliant_AREA_{noncompliant_txt}_TS_byRegion.xlsx"
    with pd.ExcelWriter(output_directory/output_file, mode='w') as writer:
        TotalAreaNoncompliant_df.to_excel(writer, sheet_name='Total Area Non-compliant')
        header_df.to_excel(writer, sheet_name='README')

    # End time counter
    end = time.perf_counter()
    print(f'Execution time: {(end - start)/60} minutes')
