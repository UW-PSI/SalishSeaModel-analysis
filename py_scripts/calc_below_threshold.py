#!/usr/bin/env python3
# Created by Rachael D. Mueller and Ben Roberts at the Puget Sound Institute
# with funding provided by King County

# Python builtins
import os
import argparse
from pathlib import Path
from dataclasses import dataclass
import time
from datetime import date
import logging

# Third party libraries
import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd

# load functions from my scripts file "ssm_utils"
from ssm_utils import read_case, VolAreaStats, create_statistics_dataframes, FileFinder, DepthReducer
from ssm_utils.depth import SCOPES

def build_DO_standard(shp: str):
    """Extract DO standard for all nodes"""
    gdf = gpd.read_file(shp).set_index('tce')
    return gdf['DO_std'].to_numpy()

def calc_DO_below_thresh(case: str, ssm_config: dict, DO_thresh: object,
                         shp: str, scope: str=None, run_type: str=None):
    """Backward-compatible calculation function
    case [string]: "SOG_NB" or "whidbey"
    ssm_config [dict]: dictionary of all case configuration
    DO_thresh [1D or int]: "DO_standard" or integer value
    shp [path]: shapefile path
    scope [string]: optional depth reduction to apply, default is full water column
    run_type [string]: optionally select only one run to compute, or None for all of them
    """

    cbt = CalcBelowThresh(case=case, ssm_config=ssm_config,
                          threshold=build_DO_standard(shp) if DO_thresh == 'DO_standard' else float(DO_thresh),
                          scope=scope, run_type=run_type)
    cbt.run()
    return (cbt.DaysBelowThresh_df, cbt.VolumeDays_df, cbt.PercentVolumeDays_df,
                cbt.DailyVolumes_dfs, cbt.DailyAreas_dfs, cbt.DaysBelowThresh_gdf)

@dataclass
class CalcBelowThresh():
    case: str
    ssm_config: dict
    threshold: np.typing.ArrayLike
    vtype: str='DOXG'
    mitype: str=None
    mispecies: str=None
    scope: str=None
    run_type: str=None

    def __post_init__(self):
        # Initialize dictionaries
        self.DaysBelowThresh_df = None
        self.VolumeDays_df = None # Percent of volume within region where DO<threshold
        self.PercentVolumeDays_df = None
        self.DailyVolumes_dfs = {}
        self.DailyAreas_dfs = {}

        self.habitat_mask = None

        self.varname = None

        self.logger = logging.getLogger('CalcBelowThreshold')

    def run(self):
        # Define dimension sizes and load shapefile
        shp = self.ssm_config['paths']['shapefile']
        gdf = gpd.read_file(shp).set_index('tce')
        if len(gdf) == 16013:
            self.logger.warning('Correcting shapefile length')
            gdf = gdf.iloc[:-1].copy()
        gdf = gdf.rename(columns={'region_inf':'Regions'})
        regions = gdf[['node_id','Regions']].groupby('Regions').count().index.to_list()

        ff = FileFinder(case=self.case, ssm_config=self.ssm_config, vtype=self.vtype,
                        mitype=self.mitype, mispecies=self.mispecies, run_type=self.run_type)
        self.varname = ff.output_var_base
        dr = DepthReducer(ssm_config=self.ssm_config, gdf=gdf)
        time_coords = None
        self.units = None

        # Load all runs
        self.logger.debug(f'Processing scenarios {ff.run_types}')
        rawdata={}
        for run_dir in ff.run_types:
            try:
                run_file = ff.get_file(run_dir, 'min')
                with xr.open_dataset(run_file) as ds:
                    Min_full=ds[ff.get_var_name(run_file)]
                    if self.scope is not None:
                        rawdata[run_dir] = dr.select_depth(Min_full, self.scope).expand_dims(dim='siglay', axis=1)
                    else:
                        rawdata[run_dir] = Min_full
                    if 'version' in ds.attrs and ds.attrs['version'] >= 2 and time_coords is not None:
                        time_coords = Min_full.coords['day']
                        self.units = Min_full.attrs['unit']
            except FileNotFoundError:
                self.logger.error(f'File Not Found: {run_file}')
                if len(dir_list) == 1:
                    raise e
            if run_dir == ff.run_types[0]:
                # Get number of days and nodes
                [ndays,nlevels,nnodes]=rawdata[run_dir].shape
        if time_coords is None:
            # Assign a reasonable default
            time_coords = pd.date_range(
                    pd.Timestamp('2014.01.01') + pd.Timedelta(days=self.ssm_config['run_information']['spin_up_days']),
                    periods=ndays, freq='D')  #create pandas date_range array of daily time index for full year

        stats = VolAreaStats(ssm_config=self.ssm_config, gdf=gdf, scope=self.scope,
                             sizes=rawdata[run_dir].sizes)

        # Create a list of column header names
        tag_list = [self.ssm_config['run_information']['run_tag'][self.case][tag] for tag in [*self.ssm_config['run_information']['run_tag'][self.case]]]

        # Apply habitat depth mask if we're looking at a particular species
        if self.mispecies is not None and self.mispecies in self.ssm_config['mi']['species']:
            max_depth = self.ssm_config['mi']['species'][self.mispecies].get('habitat_max_depth')
            if max_depth is not None:
                self.logger.info(f'Applying habitat depth mask <= {max_depth} m for species {self.mispecies}')
                bottom_depths = xr.DataArray(dr.layer_depths[1:,:], dims=('siglay','node'))
                if self.scope is not None:
                    bottom_depths = dr.select_depth(bottom_depths, self.scope)
                self.habitat_mask = xr.DataArray(np.broadcast_to(bottom_depths <= max_depth, (ndays,nlevels,nnodes)),
                                    dims=('day','siglay','node'))
                for run_type in rawdata.keys():
                    rawdata[run_type] = rawdata[run_type].where(self.habitat_mask)

        DaysBelowThresh={} # Sum of days across regions
        VolumeDays = {}
        PercentVolumeDays = {}
        DaysBelowThresh_gdf_data = {}

        # Determine BelowThresh days
        for run_type in rawdata.keys():

            # THRESHOLD ANALYSIS

            self.logger.info(f'Performing threshold <{self.threshold} analysis for {run_type}')
            VolumeDays_all = stats.apply(rawdata[run_type] <= self.threshold)

            # REGIONAL ANALYSIS

            # Total number of days and percent volume days for each region
            DaysBelowThresh[run_type]={}
            VolumeDays[run_type]={}
            PercentVolumeDays[run_type]={}
            DailyVolumes={}
            DailyAreas={}
            for region in regions:
                (DaysBelowThresh[run_type][region],
                 VolumeDays[run_type][region],
                 PercentVolumeDays[run_type][region],
                 DailyVolumes[region]) = stats.get_vol_stats_by_region(region)
                RegionArea, DailyAreas[region] = stats.get_area_stats_by_region(region)

            self.DailyVolumes_dfs[run_type] = pd.DataFrame(DailyVolumes, index=time_coords)
            self.DailyAreas_dfs[run_type] = pd.DataFrame(DailyAreas, index=time_coords)

            # ALL REGIONS SUM

            (DaysBelowThresh[run_type]['ALL_REGIONS'],
             VolumeDays[run_type]['ALL_REGIONS'],
             PercentVolumeDays[run_type]['ALL_REGIONS'],
             self.DailyVolumes_dfs[run_type]['All_regions']) = stats.get_vol_stats_by_region('all')
            (RegionAreaAll,
             self.DailyAreas_dfs[run_type]['All_regions']) = stats.get_area_stats_by_region('all')

            # THRESHOLD GDF
            DaysBelowThresh_gdf_data[run_type] = stats.data.any(axis=1).sum(axis=0)

        # DATAFRAME CREATION AND RETURN

        # Convert to dataframe and organize information
        self.DaysBelowThresh_df = pd.DataFrame(DaysBelowThresh).rename(
            columns=self.ssm_config['run_information']['run_tag'][self.case]).reindex(columns=tag_list)
        # Percent of volume over the year in each region where change < threshold
        self.VolumeDays_df = pd.DataFrame(VolumeDays).rename(
            columns=self.ssm_config['run_information']['run_tag'][self.case]).reindex(columns=tag_list)
        # Percent of cumulative volume over the year in eash region where change < threshold
        self.PercentVolumeDays_df = pd.DataFrame(PercentVolumeDays).rename(
            columns=self.ssm_config['run_information']['run_tag'][self.case]).reindex(columns=tag_list)
        self.DaysBelowThresh_gdf = self._build_threshold_gdf(DaysBelowThresh_gdf_data, gdf)

    def _build_threshold_gdf(self, parameter_data: dict, gdf: gpd.GeoDataFrame):
        """Take data as a dict of Series or numpy arrays and build it into a GeoDataFrame"""
        data = parameter_data.copy()
        data['depth'] = gdf['depth']
        gdf_plot = gpd.GeoDataFrame(data, geometry=gdf.geometry, crs=gdf.crs)
        gdf_plot = gdf_plot[gdf['included_i'] == 1]

        return gdf_plot

def main():
    parser = argparse.ArgumentParser(description='Compute volumes and timeseries of a variable below a threshold')
    parser.add_argument('case', help='Case name eg SOG_nb or whidbey')
    parser.add_argument('threshold', help='Threshold value')
    parser.add_argument('--depth', help='Depth reduction scope')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet; suppress most output')
    # TODO implement a --depth-help option to print available reductions
    subparsers = parser.add_subparsers(title='Data type selection')
    parser_var = subparsers.add_parser('var', help='Work with a model output variable')
    parser_var.add_argument('variable', help='Output variable, like DOXG')
    parser_var.set_defaults(mode='var')

    parser_mi = subparsers.add_parser('mi', help='Work with metabolic index data')
    parser_mi.add_argument('species', help='Species tag')
    parser_mi.add_argument('type', choices=('routine','smr'), help='routine or smr')
    parser_mi.set_defaults(mode='mi')
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.DEBUG)

    # Start time counter
    start = time.perf_counter()

    # load yaml file containing path definitions
    ssm, case = read_case(args.case)

    if args.mode == 'mi':
        variable = 'MI'
        variable_full = 'MI_' + args.species + '_' + args.type
        args.threshold = float(args.threshold)
        cbt = CalcBelowThresh(case=case, ssm_config=ssm,
                              threshold=args.threshold, vtype=args.mode,
                              mispecies=args.species, mitype=args.type,
                              scope=args.depth)
    else:
        variable = args.variable
        variable_full = args.variable
        if args.threshold.isnumeric():
            args.threshold = float(args.threshold)
            cbt = CalcBelowThresh(case=case, ssm_config=ssm,
                                  threshold=args.threshold, vtype=args.variable,
                                  scope=args.depth)
        elif args.threshold == 'DO_standard':
            assert variable == 'DOXG'

            cbt = CalcBelowThresh(case=case, ssm_config=ssm_config,
                                  threshold=build_DO_standard(ssm['paths']['shapefile']),
                                  scope=args.depth)
    cbt.run()

    vol_stat_dfs = create_statistics_dataframes(case, ssm, 'volume',
            cbt.DailyVolumes_dfs, habitat_mask=cbt.habitat_mask.sel(day=1) if cbt.habitat_mask is not None else None,
            scope=args.depth)
    area_stat_dfs = create_statistics_dataframes(case, ssm, 'area',
            cbt.DailyAreas_dfs, habitat_mask=cbt.habitat_mask.sel(day=1) if cbt.habitat_mask is not None else None,
            scope=args.depth)

    # make README
    this_file = '=HYPERLINK("https://github.com/UW-PSI/SalishSeaModel-analysis/tree/main/bash_scripts/calc_below_threshold.py","calc_below_threshold.py")'
    run_description  = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/docs/supporting/KingCounty_Model_Runs.xlsx","KingCounty_Model_Runs.xlsx")'
    ndays = f'Number of days where {variable} < threshold anywhere in Region'
    dvs = f'The total volume within each region that experienced {variable} < threshold each day'
    vd = f'Total volume of cells in region that experienced {variable} < threshold over the course of the year'
    pvd=f'Percent of regional volume that experienced {variable} < threshold over the course of the year'

    created_by = ssm['author']
    created_on = date.today().strftime("%B %d, %Y")

    header_df = pd.DataFrame([['Created by:', created_by],
                              ['Created on:', created_on],
                              ['Created with:', this_file],
                              ['Reference:', run_description],
                              ['Variable examined:', variable_full],
                              ['Threshold value:', args.threshold],
                              ['Threshold unit:', cbt.units],
                              ['Depth scope', SCOPES[args.depth] if args.depth else 'Full'],
                              ['Number_of_Days', ndays],
                              ['Daily_Volumes [km^3]', dvs],
                              ['Volume_Days [km^3 days]', vd],
                              ['Percent_Volume_Days[%]', pvd]
                              ], columns=[0, ' ']).set_index(0)

    # Save to output
    excel_output_path = Path(ssm['paths']['spreadsheets']) / 'calc_below_threshold'
    if not excel_output_path.is_dir():
            logger.info(f'creating: {excel_output_path}')
            os.umask(0) #clears permissions
            excel_output_path.mkdir(parents=True)
    with pd.ExcelWriter(excel_output_path/f'{case}{"_" + args.depth if args.depth is not None else ""}_{cbt.varname}-lt-{args.threshold}.xlsx', mode='w') as writer:
        cbt.DaysBelowThresh_df.to_excel(writer, sheet_name='Number_of_Days')
        for tag,df in area_stat_dfs.items():
            df.to_excel(writer, sheet_name=f'Area_{tag}', index=False)
        for run_type,df in cbt.DailyAreas_dfs.items():
            df.to_excel(writer, sheet_name=f'Daily_Areas_{run_type}')
        for tag,df in vol_stat_dfs.items():
            df.to_excel(writer, sheet_name=f'Volume_{tag}', index=False)
        for run_type,df in cbt.DailyVolumes_dfs.items():
            df.to_excel(writer, sheet_name=f'Daily_Volumes_{run_type}')
        cbt.VolumeDays_df.to_excel(writer, sheet_name='Volume_Days')
        cbt.PercentVolumeDays_df.to_excel(writer, sheet_name='Percent_Volume_Days')
        header_df.to_excel(writer, sheet_name='README')

    gdf_output_path = Path(ssm['paths']['shapefiles']) / 'calc_below_threshold'
    logger.info(f'Writing shapefile to: {gdf_output_path}')
    if not gdf_output_path.is_dir():
        logger.info(f'creating: {gdf_output_path}')
        os.umask(0) #clears permissions
        gdf_output_path.mkdir(parents=True)
    cbt.DaysBelowThresh_gdf.to_file(gdf_output_path / f'{case}{"_" + args.depth if args.depth is not None else ""}_{cbt.varname}-lt-{args.threshold}.geojson')

    # End time counter
    end = time.perf_counter()
    logger.info(f'Execution time: {(end - start)/60:.3f} minutes')

if __name__=='__main__': main()
