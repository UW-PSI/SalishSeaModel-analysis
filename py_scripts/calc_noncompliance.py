#!/usr/bin/env python3

# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
#
# Human allowance: early versions of noncompliance calculations had a sign error
# with how it was accounting for the human allowance with the DO standard. To
# replicate early results:
# - change the human allowance in the DOCompliance class from -0.2 to 0.2
# - change the Part B compliance comparison from (run < DO_part_b) to (run <= DO_part_b)
# - run with the --no-parta option.
import argparse
import os
import time
from datetime import date
import pathlib

import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd

from ssm_utils import read_case, create_statistics_dataframes, VolAreaStats, DOCompliance

def calc_noncompliant(shp: gpd.GeoDataFrame, case, scope,
                      non_compliant_threshold=-0.25, include_parta=True,
                      do303d=False):
    """
    HEADER TO BE ADDED
    This script requires inclusion of reference case subdirectory in 
    ssm['paths']['processed_output'] as well as a specification of the reference
    case sub-directory name in the yaml file under: ssm['run_information']['reference']
    """
    # Initialize dictionaries
    MinDO_full={} # Min, daily DO over all nodes
    MinDO={} # Min, daily DO over all nodes in shapefile
    DO_diff_lt_0p2_days={} # Number of days where DOBelowThresh = True
    DaysNonCompliant={} # Sum of days across regions
    TotalDays = {} # Total days of noncompliance, comparable to Figueroa-Kaminsky 2025
    VolumeDaysNonCompliant={} # Percent of volume within region where DO<threshold
    PercentVolumeDaysNonCompliant={}
    AreaNonCompliant={}
    mag_gdfs = {}

    model_var='DOXG'
    # Define dimension sizes and load shapefile
    if do303d:
        gdf = gpd.read_file(ssm['paths']['303d']['shapefile']
                ).set_index('id_303d').rename(columns={
                    'basin': 'Regions',
                    'do_crit_mg': 'DO_std',
                    'area_m2': 'Area_m2'
                })
        # FIXME just fake data right now
        gdf['volume'] = 100
        gdf['included_i'] = 1
        processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output']) / case / f'{model_var}_303d'
    else:
        gdf = gpd.read_file(shp).set_index('tce')
        gdf = gdf.rename(columns={'region_inf':'Regions'})
        processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output']) / case / model_var
    regions = gdf['Regions'].unique()

    # Get list of run sub-directories in processed netcdf directory
    dir_list = os.listdir(processed_netcdf_dir)
    print(dir_list)

    # Load all runs (including reference case)
    if scope=='benthic':
        print("Benthic case")
        for run_dir in dir_list.copy():
            try:
                run_file = processed_netcdf_dir/run_dir/'bottom'/f'daily_min_{model_var}_bottom.nc'
                with xr.open_dataset(run_file) as ds:
                    MinDO_full[run_dir]=ds[f'{model_var}_daily_min_bottom']
                    MinDO[run_dir] = MinDO_full[run_dir]
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
                dir_list.remove(run_dir)
                continue
            assert len(gdf) <= MinDO_full[run_dir].shape[1], "Shapefile dimensions don't match output file"
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nnodes]=MinDO[run_dir].shape
    else:
        print("Water Column")
        for run_dir in dir_list.copy():
            print('Getting model output for:', run_dir)
            try: 
                run_file = processed_netcdf_dir/run_dir/'wc'/f'daily_min_{model_var}_wc.nc'
                with xr.open_dataset(run_file) as ds:
                    MinDO_full[run_dir]=ds[f'{model_var}_daily_min_wc']
                    MinDO[run_dir] = MinDO_full[run_dir]
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
                dir_list.remove(run_dir)
                continue
            assert len(gdf) <= MinDO_full[run_dir].shape[2], "Shapefile dimensions don't match output file"
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nlevels,nnodes]=MinDO[run_dir].shape

    # Define reference run
    reference = ssm['run_information']['reference']
    dir_list.remove(reference)

    docomp = DOCompliance(gdf, MinDO[reference].shape,
                          non_compliant_threshold=non_compliant_threshold,
                          include_parta=include_parta)
    stats = VolAreaStats(ssm_config=ssm, gdf=gdf, sizes=MinDO[reference].sizes)

    # Loop through all non-reference runs and calculate non_compliant_threshold
    for run_type in dir_list:
        print(f'Calculating difference for {run_type}')

        DO_diff_lt_0p2, *magnitudes = docomp.find_noncompliant(MinDO[run_type],
                MinDO[reference], include_magnitudes=True)

        VolumeDays_all = stats.apply(DO_diff_lt_0p2)

        # Total number of days and percent volume days for each region
        DaysNonCompliant[run_type]={}
        AreaNonCompliant[run_type]={}
        TotalDays[run_type] = {}
        VolumeDaysNonCompliant[run_type]={}
        PercentVolumeDaysNonCompliant[run_type]={}
        for region in regions:
            (DaysNonCompliant[run_type][region],
             VolumeDaysNonCompliant[run_type][region],
             PercentVolumeDaysNonCompliant[run_type][region],
             DailyVolumes) = stats.get_vol_stats_by_region(region)
            AreaNonCompliant[run_type][region], DailyAreas = stats.get_area_stats_by_region(region)
            days, TotalDays[run_type][region] = stats.get_day_stats_by_region(region)

        # Create totals across entire domain.  This includes "Other" nodes. 
        # I tested np.asarray(VolumeDays_all)[idx], where 
        # idx = (gdf['Regions']!='Other')
        # and VolumeDays_all.sum().item().  They give the same number, 
        # so I'm keeping the 29 "Other" nodes in for now
        (DaysNonCompliant[run_type]['ALL_REGIONS'],
         VolumeDaysNonCompliant[run_type]['ALL_REGIONS'],
         PercentVolumeDaysNonCompliant[run_type]['ALL_REGIONS'],
         DailyVolumesAll) = stats.get_vol_stats_by_region('all')
        (AreaNonCompliant[run_type]['ALL_REGIONS'],
         DailyAreasAll) = stats.get_area_stats_by_region('all')
        days, TotalDays[run_type]['ALL_REGIONS'] = stats.get_day_stats_by_region('all')

        # Prepare the GeoDataFrame of noncompliance magnitudes
        mag_ncomp = np.min(magnitudes, axis=(0,1,2))
        mag_gdf_data = {
            'mag_nc': mag_ncomp
        }
        if include_parta:
            mag_gdf_data['mag_nc_a'] = magnitudes[0].min(axis=(0,1))
            print(mag_gdf_data['mag_nc_a'].shape)
            mag_gdf_data['mag_nc_b'] = magnitudes[1].min(axis=(0,1))
        else:
            mag_gdf_data['mag_nc_b'] = magnitudes[0].min(axis=(0,1))
        # Also add cumulative days of noncompliance
        mag_gdf_data['cum_day_nc'] = stats.data.any(axis=1).sum(axis=0)
        mag_gdfs[run_type] = gpd.GeoDataFrame(mag_gdf_data, geometry=gdf.geometry, crs=gdf.crs, index=gdf.index)

    print([*ssm['run_information']['run_description_short']])
    # Create a list of column header names using the keys in "run_description_short" to map to the desired name
    # run_description_short can be used to change the run_tag if a different tag is wanted than what is used on Hyak to 
    # organize runs
    tag_list = [ssm['run_information']['run_tag'][case][tag] for tag in [*ssm['run_information']['run_description_short'][case]]]
    tag_list.remove('Reference')
    print("tag_list",tag_list)

    # Convert to dataframe and organize information
    DaysNonCompliant_df = pd.DataFrame(DaysNonCompliant)
    # rename column names using dictionary (repeat this method below)
    DaysNonCompliant_df = DaysNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    # sort order of columns based on order of dictionary; otherwise, python will choose order (repeat this method below)
    DaysNonCompliant_df = DaysNonCompliant_df.reindex(columns=tag_list)
    # Total days of noncompliance
    TotalDaysNonCompliant_df = pd.DataFrame(TotalDays).rename(
        columns=ssm['run_information']['run_tag'][case]
    ).reindex(columns=tag_list)
    # Area non-compliant
    AreaNonCompliant_df = pd.DataFrame(AreaNonCompliant)
    AreaNonCompliant_df = AreaNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    AreaNonCompliant_df = AreaNonCompliant_df.reindex(columns=tag_list)
    # Percent of volume over the year in each region where DO change < threshold
    VolumeDaysNonCompliant_df = pd.DataFrame(VolumeDaysNonCompliant)
    VolumeDaysNonCompliant_df = VolumeDaysNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    # rename columns to more readable (neccessary for SOG_NB, not so much for whidbey)
    VolumeDaysNonCompliant_df = VolumeDaysNonCompliant_df.reindex(columns=tag_list)
    # Percent of cumulative volume over the year in eash region where DO change < threshold
    PercentVolumeDaysNonCompliant_df = pd.DataFrame(PercentVolumeDaysNonCompliant)
    PercentVolumeDaysNonCompliant_df = PercentVolumeDaysNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    PercentVolumeDaysNonCompliant_df = PercentVolumeDaysNonCompliant_df.reindex(
        columns=tag_list
    )

    return (DaysNonCompliant_df, TotalDaysNonCompliant_df, AreaNonCompliant_df,
            VolumeDaysNonCompliant_df,PercentVolumeDaysNonCompliant_df, mag_gdfs)

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    scope: "benthic" or "wc" for water column
    """
    parser = argparse.ArgumentParser(description='Compute days of noncompliance')
    parser.add_argument('case', help='Case name (SOG_NB, whidbey) or file')
    parser.add_argument('non_compliant_threshold', type=float,
                        help='Threshold of noncompliance')
    parser.add_argument('scope', help='"benthic" or "wc" for water column')
    parser.add_argument('--no-parta', action='store_true',
                        help='Ignore part A of the water quality standard')
    parser.add_argument('--grid-303d', action='store_true',
                        help='Compute noncompliance on the 303(d) grid')
    args = parser.parse_args()

    # convert non_compliant_threshold to text string to use in file name
    noncompliant_txt = str(args.non_compliant_threshold)
    noncompliant_txt = noncompliant_txt.replace('.','p')
    noncompliant_txt = noncompliant_txt.replace('-','m')
    if args.no_parta:
        noncompliant_txt += '_noparta'
    if args.grid_303d:
        noncompliant_txt += '_303d'

    # Start time counter
    start = time.perf_counter()

    # Load yaml file containing path definitions
    ssm, case = read_case(args.case)
    shp = ssm['paths']['shapefile']

    print('Calling calc_noncompliant')
    (DaysNonCompliant_df, TotalDays_df, AreaNonCompliant_df,
     VolumeDays_df,PercentVolumeDays_df,mag_gdfs) = calc_noncompliant(
        shp, case, args.scope, args.non_compliant_threshold,
        include_parta=not args.no_parta, do303d=args.grid_303d)

    # make README
    this_file = '=HYPERLINK("https://github.com/UW-PSI/SalishSeaModel-analysis/blob/main/py_scripts/calc_noncompliant.py")'
    run_description = '=HYPERLINK("https://github.com/UW-PSI/SalishSeaModel-analysis/tree/main/etc", "See corresponding config file")'
    non_compliant_threshold=f'{args.non_compliant_threshold} mg/l'
    noncompliant = f'Noncompliant in this table is defined as a DO difference < {args.non_compliant_threshold} mg/l'
    if not args.no_parta:
        noncompliant += ' and a DO below the DO standard'
    noncompliant += f'. A non_compliant_threshold threshold of -0.25 is described in pages 49 and 50 of the Optimization report appendix.'
    noncompliant_link = '=HYPERLINK("https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf", "Optimization Report Appendix")'
    grid = 'SSM unstructured TCEs (16012)' if not args.grid_303d else '303(d) rectangular'
    ndays = f'Number of days of noncompliance anywhere in {"benthic layer of " if args.scope == "benthic" else ""}Region'
    ntotaldays = f'Total days of noncompliance summed over all cells (assessment units) in {"benthic layer of " if args.scope == "benthic" else ""}Region'
    vd = f'Total volume of cells in {"benthic layer of " if args.scope == "benthic" else ""}region that were noncompliant over the course of the year (volume of cells times days of noncompliance)'
    pvd= f'Percent of regional {"benthic " if args.scope == "benthic" else ""}volume that was noncompliant over the course of the year'

    created_by = ssm['author']
    created_at = 'Puget Sound Institute'
    created_from = 'Model results produced by Su Kyong Yun (PNNL) and Rachael Mueller (PSI)'
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_at, created_on, this_file,
            created_from,
            run_description, non_compliant_threshold, noncompliant,
            noncompliant_link, grid, ndays, ntotaldays, vd, pvd]
    }
    header_df = pd.DataFrame(header, index=[
        'Created by',
        'Created at',
        'Created on',
        'Created with',
        'Contacts',
        'Model Run Overview',
        'Non Compliant threshold [mg/l]',
        'Non Compliant Reference',
        'Non Compliant Reference',
        'Grid',
        'NonCompliant_Days',
        'TotalDaysNonCompliant',
        'Volume_Days [km^3 days]',
        'Percent_Volume_Days[%]'])

    # Save to output to
    excel_output_path = pathlib.Path(ssm['paths']['spreadsheets']) / 'noncompliance'

    print('*************************************************************')
    print('Writing spreadsheet to: ',excel_output_path)
    print('*************************************************************')
    if not excel_output_path.is_dir():
        print(f'creating: {excel_output_path}')
        excel_output_path.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(
        excel_output_path/f'{case}_{args.scope}_noncompliant_{noncompliant_txt}.xlsx', mode='w') as writer:
        DaysNonCompliant_df.to_excel(writer, sheet_name='NonCompliant_Days')
        TotalDays_df.to_excel(writer, sheet_name='TotalDaysNonCompliant')
        AreaNonCompliant_df.to_excel(writer, sheet_name='Area_NonCompliant')
        VolumeDays_df.to_excel(writer, sheet_name='Volume_Days')
        PercentVolumeDays_df.to_excel(writer, sheet_name='Percent_Volume_Days')
        header_df.to_excel(writer, sheet_name='README')

    gdf_output_path = pathlib.Path(ssm['paths']['shapefiles']) / f'noncompliance_{args.scope}_{noncompliant_txt}'
    print('*************************************************************')
    print('Writing shapefiles to: ',gdf_output_path)
    print('*************************************************************')
    if not gdf_output_path.is_dir():
        print(f'creating: {gdf_output_path}')
        gdf_output_path.mkdir(parents=True, exist_ok=True)
    for rt, mag_gdf in mag_gdfs.items():
        subdir = gdf_output_path / rt
        if not subdir.is_dir():
            subdir.mkdir()
        mag_gdf.to_file(gdf_output_path / rt / f'{case}_{args.scope}_noncompliant_{noncompliant_txt}_{rt}.geojson')

    # End time counter
    end = time.perf_counter()
    print(f'Execution time: {(end - start)/60} minutes')
