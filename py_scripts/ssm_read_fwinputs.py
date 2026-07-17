#!/usr/bin/env python
"""Convert SSM freshwater input files into a discharge spreadsheet

Script that converts a FVCOM rivers file paired with a FVCOM-ICM point
sources file into an Excel spreadsheet that can be easily edited.

By Ben Roberts, original hosted at https://github.com/bedaro/ssm-analysis/blob/main/input_files/ssm_read_fwinputs.py
"""

from argparse import ArgumentParser, FileType
import logging
import sys
import re
from io import StringIO

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# State variables in the order they are present in the file
ALL_STATEVARS = ('discharge', 'temp', 'salt', 'tss',  'alg1', 'alg2', 'alg3', 'zoo1',
                              'zoo2', 'ldoc', 'rdoc', 'lpoc', 'rpoc', 'nh4',  'no32',
                              'urea', 'ldon', 'rdon', 'lpon', 'rpon', 'po4',  'ldop',
                              'rdop', 'lpop', 'rpop', 'pip',  'cod',  'doxg', 'psi',
                              'dsi',  'alg1p','alg2p','alg3p','dic',  'talk')

def read_dat_file(f, start_date, num_statevars=None):
    statevars = ALL_STATEVARS if num_statevars is None else ALL_STATEVARS[:num_statevars]
    # See the FVCOM manual
    inflow_type, point_st_type = np.loadtxt([next(f)], dtype=str,
            comments='!')
    # The total number of discharge nodes
    num_qs = int(next(f))
    # All the node numbers with discharges
    nodes = []
    comments = []
    commentre = r"FVCOM ID/Node: (\d+) / (\d+),\s+nodes/distribution : (\d+)/([\w\s\d]+),\s+([^,]+),\s+([\w\s]+),\s+(\w+),\s+([\w\s]+)"
    fvcomids = []
    distnodes = []
    disttypes = []
    names = []
    srctypes = []
    regions = []
    countries = []
    for l in range(num_qs):
        line = next(f).split('!', maxsplit=1)
        node = int(line[0].strip())
        nodes.append(node)
        if len(line) > 1:
            comment = line[1].strip()
            comments.append(comment)
            m = re.match(commentre, comment)
            fvcomids.append(int(m.group(1)) if m else np.nan)
            if m and int(m.group(2)) != node:
                logging.warn(f"Node {node} has a comment ({comment}) that does not appear to match")
            distnodes.append(int(m.group(3)) if m else np.nan)
            disttypes.append(m.group(4) if m else np.nan)
            names.append(m.group(5) if m else np.nan)
            srctypes.append(m.group(6) if m else np.nan)
            regions.append(m.group(7) if m else np.nan)
            countries.append(m.group(8) if m else np.nan)
        else:
            comments.append(np.nan)
            fvcomids.append(np.nan)
            distnodes.append(np.nan)
            disttypes.append(np.nan)
            names.append(np.nan)
            srctypes.append(np.nan)
            regions.append(np.nan)
            countries.append(np.nan)
    node_data = {'Node': nodes}
    if any(comments):
        node_data['Comment'] = comments
    if any(fvcomids):
        node_data['FVCOM ID'] = fvcomids
        node_data['Dist Nodes'] = distnodes
        node_data['Dist Type'] = disttypes
        node_data['Name'] = names
        node_data['Source Type'] = srctypes
        node_data['Region'] = regions
        node_data['Country'] = countries
    node_df = pd.DataFrame(node_data)
    if 'FVCOM ID' in node_df.columns:
        node_df.set_index(['Node','FVCOM ID'], drop=False, inplace=True)
    # Depth distribution fractions into each node. Skipping the first
    # (node count) column
    vqdist = np.loadtxt([next(f) for l in range(num_qs)])[:,1:]

    num_times = int(next(f))

    # Initialize storage arrays
    times = np.zeros(num_times)
    statedata = {}
    for v in statevars:
        statedata[v] = np.zeros((num_times, num_qs))

    for t in range(num_times):
        times[t] = float(next(f))
        for v in statevars:
            statedata[v][t,:] = np.loadtxt([next(f)])

    vqdist_df = pd.DataFrame(vqdist, index=node_df.index,
            columns=np.arange(vqdist.shape[1])+1)

    dates = pd.Timestamp(start_date) + pd.to_timedelta(times, 'h')
    dates.name = 'Date'
    node_data = []
    for i,idx in enumerate(node_df.index):
        data = {v: statedata[v][:,i] for v in statevars}
        data['Date'] = dates
        idx_names = ['Date']
        if np.ndim(idx) > 0:
            for n,j in zip(node_df.index.names,idx):
                idx = np.zeros(len(dates), dtype=int) + j
                data[n] = idx
                idx_names.append(n)
        else:
            data['Index'] = node_df.index
            idx_names.append('Index')
        df = pd.DataFrame(data).set_index(idx_names)
        node_data.append(df)
    node_data_df = pd.concat(node_data)

    return ({
        'nodes': node_df,
        'vqdist': vqdist_df,
        'data': node_data_df
        }, inflow_type, point_st_type)

def dfs_match(df1, df2):
    """True if common indices/columns match, otherwise returns offending column(s)"""
    mismatches = []
    m = df1.join(df2, how='inner', rsuffix='_2')
    for c in df1.columns.intersection(df2.columns):
        if np.any(m[str(c)] != m[str(c)+'_2']):
            mismatches.append(c)
    return True if len(mismatches) == 0 else mismatches

def read_merge_dats(riv_file, pnt_file, start_date):
    """Read riv and pnt_wq dat files then return a merged copy of all data"""
    dfs, inflow_type, point_st_type = read_dat_file(riv_file, start_date, num_statevars=3)
    pnt_dfs, *junk = read_dat_file(pnt_file, start_date)

    # Form a union of the node DFs
    pnt_dfs['nodes']['ICM Source'] = True
    all_nodes_df = dfs['nodes'].join(pnt_dfs['nodes'], how='outer',
            rsuffix='_pnt')
    dupcols = ('Node','Comment','FVCOM ID','Dist Nodes','Dist Type','Name','Source Type','Region','Country')
    for c in dupcols:
        all_nodes_df.fillna({c: all_nodes_df[f'{c}_pnt'] }, inplace=True)
        del all_nodes_df[f'{c}_pnt']
    all_nodes_df['ICM Source'] = ~all_nodes_df['ICM Source'].isna()

    # Check that the VQDIST and data DFs have the same values for matching
    # nodes
    mismatches = dfs_match(dfs['vqdist'], pnt_dfs['vqdist'])
    if mismatches is not True:
        raise ValueError(f'vqdist columns {mismatches} do not match')

    # Merge the VQDist DataFrames
    all_vqdist_df = pd.concat((dfs['vqdist'], pnt_dfs['vqdist']))
    # https://stackoverflow.com/a/34297689
    all_vqdist_df = all_vqdist_df[~all_vqdist_df.index.duplicated(keep='first')]
    mismatches = dfs_match(dfs['data'], pnt_dfs['data'])
    if mismatches is not True:
        logger.warning(f'nqtime columns {mismatches} do not match between hydro and WQ inputs.')
        logger.warning(f'Proceeding anyway using the WQ data')
    # Merge the data DataFrames
    cond = dfs['data'].index.isin(pnt_dfs['data'].index)
    pruned_riv_data = dfs['data'].drop(dfs['data'][cond].index)
    all_data_df = pd.concat((pruned_riv_data, pnt_dfs['data']))

    return ({
        'nodes': all_nodes_df,
        'vqdist': all_vqdist_df,
        'data': all_data_df,
        'version': 2
        }, inflow_type, point_st_type)

def write_spreadsheet(dfs, out_file_excel):
    with pd.ExcelWriter(out_file_excel) as writer:
        dfs['nodes'].to_excel(writer, sheet_name='Nodes')
        dfs['vqdist'].to_excel(writer, sheet_name='VQDist')

        dfs['data'].to_excel(writer, sheet_name='Data')

def main():
    parser = ArgumentParser(description="Convert freshwater dat files into Excel spreadsheet")
    parser.add_argument("riv_file", type=FileType('r'),
            help="The FVCOM rivers file")
    parser.add_argument("pnt_wq_file", type=FileType('r'),
            help="The FVCOM-ICM point source file")
    parser.add_argument("outfile", type=FileType('wb'),
            help="The destination spreadsheet file")
    parser.add_argument("-s", "--start-date", type=pd.Timestamp,
            default="2014.01.01", help="The zero date for the file")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
            help="Print progress messages during the conversion")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    logger.info("Reading files")
    dfs, *junk = read_merge_dats(args.riv_file, args.pnt_wq_file, args.start_date)

    logger.info("Writing the spreadsheet")
    write_spreadsheet(dfs, args.outfile)

    logger.info("Finished.")

if __name__ == "__main__": main()
