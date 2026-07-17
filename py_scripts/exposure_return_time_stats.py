#!/usr/bin/env python3
# Created by Ben Roberts at the Puget Sound Institute with funding from King County

import argparse
from pathlib import Path
import time
from datetime import date
import logging
from dataclasses import dataclass

import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd

from ssm_utils import read_case, FileFinder, ExposureReturn, DepthReducer
from ssm_utils.depth import SCOPES

@dataclass
class ExposureReturnTimeStats():
    case: str
    ssm_config: dict
    threshold: float
    vtype: str = 'DOXG'
    mitype: str = None
    mispecies: str = None
    run_type: str = None
    scope: str = None

    def __post_init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        shp = self.ssm_config['paths']['shapefile']
        # Define dimension sizes and load shapefile
        gdf = gpd.read_file(shp).set_index('tce')
        if len(gdf) == 16013:
            self.logger.warning('Correcting shapefile length')
            gdf = gdf.iloc[:-1].copy()
        self.gdf = gdf.rename(columns={'region_inf':'Regions'})
        self.regions = self.gdf[['node_id','Regions']].groupby('Regions').count().index.to_list()

        # Get path for model output
        self.ff = FileFinder(case=self.case, ssm_config=self.ssm_config, vtype=self.vtype,
                        mitype=self.mitype, mispecies=self.mispecies, run_type=self.run_type)
        self.dr = DepthReducer(ssm_config=self.ssm_config, gdf=self.gdf)

        if self.mispecies is not None and self.mispecies in self.ssm_config['mi']['species']:
            self.max_depth = self.ssm_config['mi']['species'][self.mispecies].get('habitat_max_depth')
        else:
            self.max_depth = None

    def run(self):
        output_var_base = self.ff.output_var_base
    
        # Now, load files, starting with the daily minimum of the variable
        data = {}
        for run_type in self.ff.run_types:
            # We only need minimum for what we're doing
            p = self.ff.get_file(run_type, 'min')
            with xr.open_dataset(p) as ds:
                data[run_type] = ds[self.ff.get_var_name(p)]
                # Apply depth scope
                if self.scope is not None:
                    data[run_type] = self.dr.select_depth(data[run_type], self.scope).expand_dims(dim='siglay', axis=1)

       # Apply habitat depth mask if we're looking at a particular species
        if self.max_depth is not None:
            self.logger.info(f'Applying habitat depth mask <= {self.max_depth} m for species {self.mispecies}')
            bottom_depths = xr.DataArray(self.dr.layer_depths[1:,:], dims=('siglay','node'))
            if self.scope is not None:
                # FIXME this only works on bt scope
                bottom_depths = self.dr.select_depth(bottom_depths, self.scope)
            self.habitat_mask = xr.DataArray(np.broadcast_to(bottom_depths <= self.max_depth, data[run_type].shape),
                                dims=('day','siglay','node'))
            for rt in data.keys(): data[rt] = data[rt].where(self.habitat_mask)
        else:
            self.habitat_mask = None

        # Main loop is below, processing one scenario at a time
        er = ExposureReturn(self.ssm_config, self.gdf, data[run_type].sizes, scope=self.scope)
        erdata = {}
        MedExposures = {}
        MedReturns = {}
        MedNetExposures = {}
        MedExposuresBot = {}
        MedReturnsBot = {}
        MedNetExposuresBot = {}
        MaxExposures = {}
        MaxNetExposures = {}
        self.exp_gdfs = {}
        er_dir = Path(self.ssm_config['paths']['processed_output']) / self.case / 'ExposureReturn' / f'{output_var_base}_ExposureReturn_lt{self.threshold}'
        for run_type in self.ff.run_types:
            self.logger.info(f'Processing run {run_type}')
            # Load precomputed exposure/return data
            with xr.open_dataset(er_dir / f'{run_type}.nc') as erds:
                base = f'{output_var_base}_{run_type}'
                # xarray isn't auto-masking automatically, probably because
                # the file is storing data as integers? In any case, it's easy
                # to fix manually.
                er_raw = {
                        'exposure': erds[base + '_exposure'].where(erds[base + '_exposure'] > 0),
                        'return': erds[base + '_returntime'].where(erds[base + '_returntime'] > 0),
                        'partial': erds[base + '_partial'].where(erds[base + '_partial'] > 0),
                        'net': erds[base + '_net'].where(erds[base + '_net'] > 0)
                }
                # Apply depth scope
                if self.scope is not None:
                    for k in er_raw.keys(): er_raw[k] = self.dr.select_depth(er_raw[k], self.scope).expand_dims(dim='siglay', axis=1)
                # Apply the habitat mask
                if self.habitat_mask is not None:
                    for k in er_raw.keys(): er_raw[k] = er_raw[k].where(self.habitat_mask)
                er.load(data[run_type] < self.threshold, er_raw['exposure'], er_raw['return'],
                        er_raw['partial'], er_raw['net'])

            # REGIONAL ANALYSIS
            erdata[run_type] = {}
            MedExposures[run_type] = []
            MedReturns[run_type] = []
            MedNetExposures[run_type] = []
            MedExposuresBot[run_type] = []
            MedReturnsBot[run_type] = []
            MedNetExposuresBot[run_type] = []
            MaxExposures[run_type] = []
            MaxNetExposures[run_type] = []
            for region in self.regions + ['all']:
                self.logger.info(f'   Region {region}')
                d = er.get_duration_stats_by_region(region)
                erdata[run_type] = {x: erdata[run_type].get(x, []) + [d[x]] for x in d}

            # This is here to catch serious mistakes with the computations, but it may need to
            # be removed in the future for high thresholds that never get exceeded under some
            # scenarios
            assert not np.isnan(erdata[run_type]['Max_Exposure_MaxCell'][-1])

            self.exp_gdfs[run_type] = er.get_exposure_by_node()

        # DATAFRAME CREATION AND RETURN
        region_idx = self.regions + ['All_Regions']
        self.dfs = {rt: pd.DataFrame(erdata[rt], index=region_idx).round(3) for rt in self.ff.run_types}

        self.output_var_base = output_var_base

def main():
    parser = argparse.ArgumentParser(description='Build exposure and return times below a threshold')
    parser.add_argument('case', help='Case name or file')
    parser.add_argument('threshold', type=float, default=2, help='Threshold value')
    parser.add_argument('--depth', help='Depth reduction scope')
    subparsers = parser.add_subparsers(title='Data type selection')
    parser_var = subparsers.add_parser('var', help='Work with a model output variable')
    parser_var.add_argument('variable', help='Output variable, like DOXG')
    parser_var.set_defaults(mode='var')

    parser_mi = subparsers.add_parser('mi', help='Work with metabolic index data')
    parser_mi.add_argument('species', help='Species tag')
    parser_mi.add_argument('type', choices=('routine','smr'), help='routine or smr')
    parser_mi.set_defaults(mode='mi', variable='MI')

    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    xr.set_options(netcdf_engine_order=['h5netcdf','netcdf4','scipy'],
                   use_new_combine_kwarg_defaults=True)

    # Start time counter
    start = time.perf_counter()
    ssm_config, case = read_case(args.case)

    if args.mode == 'mi':
        ERS = ExposureReturnTimeStats(case, ssm_config, args.threshold, 'mi', mitype=args.type,
                                   mispecies=args.species, scope=args.depth)
    else:
        ERS = ExposureReturnTimeStats(case, ssm_config, args.threshold, args.variable, scope=args.depth)
    ERS.run()

    # make README 
    this_file = '=HYPERLINK("https://github.com/UW-PSI/SalishSeaModel-analysis/tree/main/py_scripts/exposure_return_time_stats.py","exposure_return_time_stats.py")'
    depth_scope = (SCOPES[args.depth] if args.depth else 'Full') + (f' < {ERS.max_depth} m for {args.species} habitat' if ERS.max_depth is not None else '')
    exposure = f'Contiguous days where {args.variable} < {args.threshold} at a particular location (stress condition)'
    return_time = f'Contiguous days where {args.variable} >= {args.threshold} at a particular location after previously being below (return condition)'
    part_return = f'Days when minimum is below {args.threshold} but maximum is above (partial relief)'
    net_exposure = 'Exposure days not mitigated by partial return periods. If the daily max never falls below the threshold, there is no net exposure.'
    count = 'Region-wide count of exposure events divided by number of nodes in region. This is a normalized measurement of how frequently exposure events occur independent of their duration'
    med_ = 'Region-wide volume-weighted mean of the per-cell-layer median time'
    mean_ = 'Region-wide volume-weighted mean of the per-cell-layer mean time'
    max_ = 'Region-wide maximum time in any cell-layer'
    mincell = 'The smallest nonzero value in any cell'
    maxcell = 'The largest value in any cell'

    created_by = ssm_config['author']
    created_on = date.today().strftime("%B %d, %Y")

    header_df = pd.DataFrame([['Created by:', created_by],
                              ['Created on:', created_on],
                              ['Created with:', this_file],
                              ['Variable examined:', args.variable.upper()],
                              ['Threshold value:', args.threshold],
                              ['Depth scope:', depth_scope],
                              ['Exposure [days]', exposure],
                              ['Return_Time [days]', return_time],
                              ['Partial_Return [days]', part_return],
                              ['Net_Exposure [days]', net_exposure],
                              ['Exposure_Count_Per_Vol [#/km3]', count],
                              ['Med_* [days]', med_],
                              ['Mean_* [days]', mean_],
                              ['Max_* [days]', max_],
                              ['*_MinCell', mincell],
                              ['*_MaxCell', maxcell]
                              ], columns=[0, ' ']).set_index(0)

    # Save to output
    base = ERS.output_var_base
    excel_output_path = Path(ssm_config['paths']['spreadsheets']) / 'ExposureReturn'
    logger.info(f'Writing spreadsheet to: {excel_output_path}')
    if not excel_output_path.is_dir():
        logger.info(f'creating: {excel_output_path}')
        excel_output_path.mkdir(parents=True)
    with pd.ExcelWriter(excel_output_path/f'{case}{"_" + args.depth if args.depth is not None else ""}_ExposureReturn_{base}-lt-{args.threshold}.xlsx', mode='w') as writer:
        for run_type,df in ERS.dfs.items():
            df.to_excel(writer, sheet_name=run_type)
        header_df.to_excel(writer, sheet_name='README')

    gdf_output_path = Path(ssm_config['paths']['shapefiles']) / 'ExposureReturn'
    logger.info(f'Writing shapefiles to: {gdf_output_path}')
    if not gdf_output_path.is_dir():
        logger.info(f'creating: {gdf_output_path}')
        gdf_output_path.mkdir(parents=True)
    for rt, exp_gdf in ERS.exp_gdfs.items():
        exp_gdf.to_file(gdf_output_path / f'{case}{"_" + args.depth if args.depth is not None else ""}_{rt}_ExposureReturn_{base}-lt-{args.threshold}.geojson')

    # End time counter
    end = time.perf_counter()
    logger.info(f'Execution time: {(end - start)/60:.3f} minutes')

if __name__ == '__main__': main()
