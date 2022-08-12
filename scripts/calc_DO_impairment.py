import sys
import os
sys.path.insert(1, '../scripts/')
import xarray
import openpyxl
import contextily as cx 
import yaml
import numpy as np
import pandas
import pathlib
import time
from datetime import date
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
# load functions from my scripts file "ssm_utils"
from ssm_utils import get_nearest_node, reshape_fvcom, calc_fvcom_stat, extract_fvcom_level

def calc_impaired(shp, case, scope, impairment=-0.2):
    """
    HEADER TO BE ADDED
    This script requires inclusion of reference case subdirectory in 
    ssm['paths']['processed_output'] as well as a specification of the reference
    case sub-directory name in the yaml file under: ssm['run_information']['reference']
    """
    # Initialize dictionaries
    MinDO_full={} # Min, daily DO over all nodes
    MinDO={} # Min, daily DO over all nodes in shapefile
    DO_diff_lt_0p2={} # Boolean where DO<threshold
    DO_diff_lt_0p2_days={} # Number of days where DOBelowThresh = True
    DaysImpaired={} # Sum of days across regions
    VolumeDaysImpaired={} # Percent of volume within region where DO<threshold
    PercentVolumeDaysImpaired={}
     
    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby(
        'Regions').count().index.to_list()
    regions.remove('Other')
    
    # Get path for model output
    model_var='DOXG' 
    processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output'])/case/model_var
    
    # Get list of run sub-directories in processed netcdf directory
    dir_list = os.listdir(processed_netcdf_dir)
    
    # Load all runs (including reference case)
    if scope=='benthic':
        print("Benthic case")
        for run_dir in dir_list: 
            try: 
                run_file=processed_netcdf_dir/run_dir/'bottom'/f'daily_min_{model_var}_bottom.nc'
                with xarray.open_dataset(run_file) as ds:
                    print([*ds])
                    MinDO_full[run_dir]=ds[f'{model_var}_daily_min_bottom']
                    # Sub-sample nodes (from 16012 nodes to 7494)
                    MinDO[run_dir]=MinDO_full[run_dir][:,gdf['node_id']-1]
                    print(MinDO[run_dir].shape)
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nnodes]=MinDO[run_dir].shape
    else: # water column (with 10 levels)
        print("Water Column")
        for run_dir in dir_list:
            try: 
                run_file=processed_netcdf_dir/run_dir/f'daily_min_{model_var}.nc'
                with xarray.open_dataset(run_file) as ds:
                    print([*ds])
                    MinDO_full[run_dir]=ds[f'{model_var}_daily_min']
                    # Sub-sample nodes (from 16012 nodes to 7494)
                    MinDO[run_dir]=MinDO_full[run_dir][:,:,gdf['node_id']-1]
                    print(MinDO[run_dir].shape)
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nlevels,nnodes]=MinDO[run_dir].shape

    # Calculate volume for volume days
    if scope=='benthic':
        volume = np.asarray(
            gdf.volume*ssm['siglev_diff'][-1]/100) # just the bottom level
    else: # water column
        volume = np.asarray(gdf.volume)
        depth_fraction = np.array(ssm['siglev_diff'])/100
        volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))
    
    # Define reference run
    reference = ssm['run_information']['reference']
    print(reference)
    dir_list.remove(reference)
    
    # Loop through all non-reference runs and calculate impairment
    for run_type in dir_list:
        print(f'Calculating difference for {run_type}')
        # Create array of Dissolved Oxygen threshold values 
        DO_diff = MinDO[run_type] - MinDO[reference]
        # Boolean where DO_diff < -0.2 (or impairment value)
        DO_diff_lt_0p2[run_type] = DO_diff<=impairment #361x4144 (nodes x time) or 361x10x4144
        # Number of days where DO < threshold = True
        if scope=='benthic':
            DO_diff_lt_0p2_days[run_type]=DO_diff_lt_0p2[run_type].sum(
                axis=0, initial=0) #4144 (nodes) or 10x4144
            VolumeDays_all=volume*DO_diff_lt_0p2_days[run_type]
        else: # water column: sum over days and take max value over depth
            # First get a count of days impaired for each depth level
            DO_diff_lt_0p2_days_wc=DO_diff_lt_0p2[run_type].sum(
                axis=0, initial=0)
            # Volume days: Use days impaired for each level  and element-wise 
            # multiplication of 10x4144 * 10x4144 matrices to get volume days by level
            VolumeDays_wc=volume2D.transpose()*DO_diff_lt_0p2_days_wc
            # Add across levels to get total VolumeDays per node
            VolumeDays_all = VolumeDays_wc.sum(axis=0)
        
        # Total number of days and percent volume days for each region
        DaysImpaired[run_type]={}
        VolumeDaysImpaired[run_type]={}
        PercentVolumeDaysImpaired[run_type]={}
        for region in regions:
            # create boolean of indices where True selects nodes of 
            # specified Region 
            idx = ((gdf['Regions']==region) &
                (gdf['included_i']==1))            
            # Note: The max of True/False will be True and initial sets False to zero.
            # The "where" keywork specifies to only use values where idx=True,
            # which in this case I set to specify the region.
            if scope=='benthic':
                # Assign the maximum (True) of DO < threshold occurrence anywhere in region
                # then sum values over time
                DaysImpaired[run_type][region] = DO_diff_lt_0p2[run_type].max(
                    axis=1,where=idx,initial=0).sum().item()
            else:
                # Assign the maximum (True) of DO < threshold occurrence across depths 
                # such that 1-day of impairement is counted if there is one or more 
                # levels impaired
                DOBelowThresh_daysnodes = DO_diff_lt_0p2[run_type].max(axis=1,initial=0)
                # Assign the maximum (True) of DO < threshold occurrence 
                # anywhere in region then sum values over time
                DaysImpaired[run_type][region] = DOBelowThresh_daysnodes.max(
                    axis=1,where=idx,initial=0).sum().item()
            
            VolumeDaysImpaired[run_type][region]=np.array(VolumeDays_all)[
                (gdf['Regions']==region) &
                (gdf['included_i']==1)
            ].sum()
            # get regional volume
            if scope=='benthic': # take fraction for bottom-level volume
                RegionVolume = ssm['siglev_diff'][-1]/100*volume[
                    (gdf['Regions']==region) &
                    (gdf['included_i']==1)
                ].sum()
            else: # water column
                RegionVolume = volume[
                    (gdf['Regions']==region) &
                    (gdf['included_i']==1)
                ].sum()
            PercentVolumeDaysImpaired[run_type][region]=100*(
                VolumeDaysImpaired[run_type][region]/(RegionVolume*ndays)
            )
        # Create totals across entire domain 
        if scope=='benthic': #(361x4771): max over nodes and sum over time
            DaysImpaired[run_type]['ALL_REGIONS'] = DO_diff_lt_0p2[run_type].max(
                axis=1, initial=0).sum(axis=0,initial=0).item()
        else: #(361x10x4771): max over nodes and depth and sum over time
            DaysImpaired[run_type]['ALL_REGIONS'] = DO_diff_lt_0p2[run_type].max(
                axis=2,initial=0).max(axis=1,initial=0).sum(axis=0,initial=0).item()
        VolumeDaysImpaired[run_type]['ALL_REGIONS'] = VolumeDays_all.sum().item()
        PercentVolumeDaysImpaired[run_type]['ALL_REGIONS'] = 100*(
            VolumeDays_all.sum().item()/(volume.sum().item()*ndays)
        )
    # Convert to dataframe and organize information
    DaysImpaired_df = pandas.DataFrame(DaysImpaired)
    DaysImpaired_df = DaysImpaired_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    print('*** DaysImpaired_df ***')
    print([*DaysImpaired_df])
    if case=='SOG_NB':
        DaysImpaired_df = DaysImpaired_df.reindex(
            columns=['Present Day','1b','1c','1d','1e','2a','2b'])
    else: # whidbey
        DaysImpaired_df = DaysImpaired_df.reindex(
            columns=['Present Day','3b','3c','3g','3h','3i'])
    # Percent of volume over the year in each region where DO change < threshold
    VolumeDaysImpaired_df = pandas.DataFrame(VolumeDaysImpaired)
    VolumeDaysImpaired_df = VolumeDaysImpaired_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    if case=='SOG_NB':
        VolumeDaysImpaired_df = VolumeDaysImpaired_df.reindex(
            columns=['Present Day','1b','1c','1d','1e','2a','2b'])
    else: # whidbey
        VolumeDaysImpaired_df = VolumeDaysImpaired_df.reindex(
            columns=['Present Day','3b','3c','3g','3h','3i'])
    # Percent of cumulative volume over the year in eash region where DO change < threshold
    PercentVolumeDaysImpaired_df = pandas.DataFrame(PercentVolumeDaysImpaired)
    PercentVolumeDaysImpaired_df = PercentVolumeDaysImpaired_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    if case=='SOG_NB':
        PercentVolumeDaysImpaired_df = PercentVolumeDaysImpaired_df.reindex(
            columns=['Present Day','1b','1c','1d','1e','2a','2b'])
    else: # whidbey
        PercentVolumeDaysImpaired_df = PercentVolumeDaysImpaired_df.reindex(
            columns=['Present Day','3b','3c','3g','3h','3i'])
    return DaysImpaired_df,VolumeDaysImpaired_df,PercentVolumeDaysImpaired_df

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    scope: "benthic" or "wc" for water column
    """
    args = sys.argv[1:]
    case=args[0]
    scope=args[1]

    # Start time counter
    start = time.time()
    
    # Load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.ipynb
    # but can also be modified here (with the caveat the modifications will be 
    # over-written when the SSM_config.ipynb is run
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.yaml
    with open('../etc/SSM_config.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
        # get shapefile path    
        shp = ssm['paths']['shapefile']

    DaysImpaired_df,VolumeDays_df,PercentVolumeDays_df = calc_impaired(
        shp, case, scope)
        
    # make README 
    this_file = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/scripts/calc_DO_impairment.py","calc_DO_impairment.py")'
    run_description = '=HYPERLINK("https://uwnetid.sharepoint.com/:x:/r/sites/og_uwt_psi/_layouts/15/Doc.aspx?sourcedoc=%7B417ABADA-C061-4340-9D09-2A23A26727E6%7D&file=Municipal%20%20model%20runs%20and%20scripting%20task%20list.xlsx&action=default&mobileredirect=true&cid=b2fb77a1-5678-4b1a-b7e6-39446422cd36","Municipal model runs and scripting task list")'
    ndays = 'Number of days where DO(scenario) - DO(reference) < -0.2 anywhere in Region (or in benthic layer of region if benthic case)'
    vd = 'Total volume of cells in region (or benthic layer in region) that experienced DO(scenario) - DO(reference) < -0.2 over the course of the years'
    pvd= 'Percent of regional (or benthic) volume that experienced DO(scenario) - DO(reference) < -0.2 over the course of the year'

    created_by = 'Rachael D. Mueller'
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_on, this_file, run_description, ndays, vd, pvd]
    }
    header_df = pandas.DataFrame(header, index=['Created by:',
                                   'Created on:',
                                   'Created with:',
                                   'Reference:',
                                   'Impaired_Days',
                                   'Volume_Days [km^3 days]',
                                   'Percent_Volume_Days[%]'])

    # Save to output to 
    excel_output_path = pathlib.Path(ssm['paths']['processed_output'])/case
    print('*************************************************************')
    print('Writing spreadsheet to: ',excel_output_path)
    print('*************************************************************')
    if os.path.exists(excel_output_path)==False:
        print(f'creating: {excel_output_path}')
        os.umask(0) #clears permissions
        os.makedirs(excel_output_path, mode=0o777,exist_ok=True)
    with pandas.ExcelWriter(
        excel_output_path/f'{case}_{scope}_impaired.xlsx', mode='w') as writer:  
        DaysImpaired_df.to_excel(writer, sheet_name='Impaired_Days')
        VolumeDays_df.to_excel(writer, sheet_name='Volume_Days')
        PercentVolumeDays_df.to_excel(writer, sheet_name='Percent_Volume_Days')
        header_df.to_excel(writer, sheet_name='README')

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
