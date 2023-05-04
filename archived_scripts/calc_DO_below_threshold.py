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

def calc_DO_below_thresh(case, DO_thresh, shp, scope):
    """ 
    case [string]: "SOG_NB" or "whidbey"
    DO_thresh [1D or int]: "DO_standard" or integer value
    shp [path]: shapefile path
    dir_list [list]: List of directory names for model output
    scope [string]: "benthic" or "wc" (for water column)
    """
 
    # Initialize dictionaries
    MinDO={}
    DOXGBelowThresh={} # Boolean where DOXG<threshold
    DOXGBelowThreshDays={} # Number of days where DOXGBelowThresh = True
    DaysDOXGBelowThresh={} # Sum of days across regions
    VolumeDays={} # Percent of volume within region where DO<threshold
    PercentVolumeDays={}
    
    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf=gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby('Regions').count().index.to_list()
    regions.remove('Other') # These will be removed in future iterations
   
    # Get path for model output
    model_var='DOXG' 
    processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output'])/case/model_var
    
    # Get list of run sub-directories in processed netcdf directory
    dir_list = os.listdir(processed_netcdf_dir)
    
    # Load all runs   
    if scope=='benthic':
        for run_dir in dir_list:
            try: 
                run_file=processed_netcdf_dir/run_dir/'bottom'/f'daily_min_{model_var}_bottom.nc'
                with xarray.open_dataset(run_file) as ds:
                    print([*ds])
                    MinDO_full=ds[f'{model_var}_daily_min_bottom']
                    # Sub-sample nodes (from 16012 nodes to 7494)
                    MinDO[run_dir]=MinDO_full[:,gdf['node_id']-1]
                    print(MinDO[run_dir].shape)
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nnodes]=MinDO[run_dir].shape
    else: # water column (with 10 levels)
        for run_dir in dir_list:
            try: 
                run_file=processed_netcdf_dir/run_dir/f'daily_min_{model_var}.nc'
                with xarray.open_dataset(run_file) as ds:
                    print([*ds])
                    MinDO_full=ds[f'{model_var}_daily_min']
                    # Sub-sample nodes (from 16012 nodes to 7494)
                    MinDO[run_dir]=MinDO_full[:,:,gdf['node_id']-1]
                    print(MinDO[run_dir].shape)
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nlevels,nnodes]=MinDO[run_dir].shape
                
    # Create array of Dissolved Oxygen threshold values
    if DO_thresh=='DO_standard':
        DO_thresh=gdf['DO_std']
        if scope=='benthic':
            # create array of DO_threshold values
            # (7494,361) x (7494,1) => element-wise multiplication
            DO_thresh2D = np.ones(
                (nnodes,ndays))*np.array(DO_thresh).reshape(nnodes,1)
        else:
            DO_thresh3D = np.ones(
                (nnodes,nlevels,ndays))*np.array(DO_thresh).reshape(nnodes,1,1)
    else:
        print("***", DO_thresh, type(DO_thresh))
        if scope=='benthic':
            DO_thresh2D = np.ones((nnodes,ndays))*int(DO_thresh)
        else:
            DO_thresh3D = np.ones((nnodes,nlevels,ndays))*int(DO_thresh)
        
    # Calculate volume for volume days
    if scope=='benthic': # just the bottom level
        volume = np.asarray(gdf.volume*ssm['siglev_diff'][-1]/100) 
    else: # water column
        volume = np.asarray(gdf.volume)
        depth_fraction = np.array(ssm['siglev_diff'])/100
        volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))   
        
    # Determine DOXGBelowThresh days
    for run_type in dir_list:
        print(run_type)
        # Boolean where DOXG<threshold
        if scope=='benthic':
            # 361x4144 (nodes x time)
            DOXGBelowThresh[run_type] = MinDO[run_type]<=DO_thresh2D.transpose() 
            # Number of days where DOXGBelowThresh = True
            DOXGBelowThreshDays[run_type]=DOXGBelowThresh[run_type].sum(axis=0,initial=0)
            # Volume days
            VolumeDays_all=volume*DOXGBelowThreshDays[run_type]
        else: # water column
            #361x10x4144 (nodes x depth x time)
            DOXGBelowThresh[run_type] = MinDO[run_type]<=DO_thresh3D.transpose() 
            # First get a count of days below threshold for each depth level
            DOXGBelowThreshDays_wc=DOXGBelowThresh[run_type].sum(
                axis=0,initial=0) #10x4144 (nodes)
            # Volume days: Use days impaired for each level  and element-wise 
            # multiplication of 10x4144 * 10x4144 matrices to get volume days by level 
            VolumeDays_wc=volume2D.transpose()*DOXGBelowThreshDays_wc
            # Add across levels to get total VolumeDays per node
            VolumeDays_all = VolumeDays_wc.sum(axis=0)
     
        # Total number of days and percent volume days for each region
        DaysDOXGBelowThresh[run_type]={}
        VolumeDays[run_type]={}
        PercentVolumeDays[run_type]={}
        for region in regions:
            # create boolean of indices where True selects nodes of 
            # specified Region 
            idx = ((gdf['Regions']==region) &
                (gdf['included_i']==1))            
            # Note: The max of True/False will be True and initial sets False to zero.
            # The "where" keywork specifies to only use values where idx=True,
            # which in this case I set to specify the region.
            if scope=='benthic':
                # Assign the maximum (True) of DO < threshold occurrence across region
                DaysDOXGBelowThresh[run_type][region] = DOXGBelowThresh[run_type].max(
                    axis=1,where=idx,initial=0).sum().item()
            else:
                # Assign the maximum (True) of DO < threshold occurrence across depths
                # Take max over depth to assign True if DO < threshold in one 
                # or more levels
                DOXGBelowThresh_daysnodes = DOXGBelowThresh[run_type].max(axis=1,initial=0)
                # Assign the maximum (True) if DO < threshold occurrence across region
                # then add values over time to get days < threshold
                DaysDOXGBelowThresh[run_type][region] = DOXGBelowThresh_daysnodes.max(
                    axis=1,where=idx,initial=0).sum().item()
            VolumeDays[run_type][region]=np.array(VolumeDays_all)[
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
            PercentVolumeDays[run_type][region]=100*(
                VolumeDays[run_type][region]/(RegionVolume*ndays)
            )
     
        # Add sum across all region to the dataframe
        if scope=='benthic':
            DaysDOXGBelowThresh[run_type]['ALL_REGIONS'] = DOXGBelowThresh[run_type].max(
                axis=1,initial=0).sum(axis=0,initial=0).item()     
        else:
            DaysDOXGBelowThresh[run_type]['ALL_REGIONS'] = DOXGBelowThresh[run_type].max(
                axis=2,initial=0).max(axis=1,initial=0).sum(axis=0,initial=0).item()
        VolumeDays[run_type]['ALL_REGIONS'] = VolumeDays_all.sum().item()
        PercentVolumeDays[run_type]['ALL_REGIONS'] = 100*(
            VolumeDays_all.sum().item()/
            (volume.sum().item()*ndays)
        )
        
    # Convert to dataframe and organize information
    DaysDOXGBelowThresh_df = pandas.DataFrame(DaysDOXGBelowThresh)
    DaysDOXGBelowThresh_df = DaysDOXGBelowThresh_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    if case=='SOG_NB':
        DaysDOXGBelowThresh_df = DaysDOXGBelowThresh_df.reindex(
            columns=['Present Day','Reference','1b','1c','1d','1e','2a','2b'])
    else: # whidbey
        DaysDOXGBelowThresh_df = DaysDOXGBelowThresh_df.reindex(
            columns=['Present Day','Reference','3b','3c','3g','3h','3i'])
    # Percent of volume over the year in each region where DOXG change < threshold
    VolumeDays_df = pandas.DataFrame(VolumeDays)
    VolumeDays_df = VolumeDays_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    if case=='SOG_NB':
        VolumeDays_df = VolumeDays_df.reindex(
            columns=['Present Day','Reference','1b','1c','1d','1e','2a','2b'])
    else: # whidbey
        VolumeDays_df = VolumeDays_df.reindex(
            columns=['Present Day','Reference','3b','3c','3g','3h','3i'])
    # Percent of cumulative volume over the year in eash region where DOXG change < threshold
    PercentVolumeDays_df = pandas.DataFrame(PercentVolumeDays)
    PercentVolumeDays_df = PercentVolumeDays_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    if case=='SOG_NB':
        PercentVolumeDays_df = PercentVolumeDays_df.reindex(
            columns=['Present Day','Reference','1b','1c','1d','1e','2a','2b'])
    else: # whidbey  
        PercentVolumeDays_df = PercentVolumeDays_df.reindex(
            columns=['Present Day','Reference','3b','3c','3g','3h','3i'])
    return DaysDOXGBelowThresh_df,VolumeDays_df,PercentVolumeDays_df

if __name__=='__main__':
    """
    VERY basic error handling.  Update needed. 
    # args[0]: SOG_NB or whidbey 
    # args[1]: DO threshold
    # args[2]: benthic or wc
    """
    # skip first argument, which is the file name
    print(sys.argv[0])
    args = sys.argv[1:]
    case=args[0]
    DO_thresh=args[1]
    scope=args[2]
    print('*****************************')
    print(args[0],type(args[0]),type(args[1]))
    print('*****************************')
    
    # Start time counter
    start = time.time()

    # load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.ipynb
    # but can also be modified here (with the caveat the modifications will be 
    # over-written when the SSM_config.ipynb is run
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.yaml
    with open('../etc/SSM_config.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
        # get shapefile path    
        shp = ssm['paths']['shapefile']

    H={} #DOXG below threshold
    VD={} #volume days
    PVD={} # percent volume days
    H['DO_std'],VD['DO_std'], PVD['DO_std']=calc_DO_below_thresh(
        case,
        DO_thresh, # "DO_standard" or integer (e.g. 2 or 5)
        shp, # shapefile path (with "DO_std" attribute)
        scope # "benthic" or "wc" (for water column)
    )
    
    # make README 
    this_file = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/scripts/calc_DO_below_threshold.py","calc_DO_below_threshold.py")'
    run_description  = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/docs/supporting/KingCounty_Model_Runs.xlsx","KingCounty_Model_Runs.xlsx")'
    ndays = 'Number of days where DO < threshold anywhere in Region (or in benthic layer of region if benthic case)'
    vd = 'Total volume of cells in region that experienced DO < threshold over the course of the year'
    pvd='Percent of regional volume that experienced DO < threshold over the course of the year'

    created_by = 'Rachael D. Mueller'
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_on, this_file, run_description, ndays, vd, pvd]
    }
    header_df = pandas.DataFrame(header, index=['Created by:',
                                   'Created on:',
                                   'Created with:',
                                   'Reference:',
                                   'Number_of_Days',
                                   'Volume_Days [km^3 days]',
                                   'Percent_Volume_Days[%]'])

    # Save to output to 
    excel_output_path = pathlib.Path(ssm['paths']['processed_output'])/case
    if os.path.exists(excel_output_path)==False:
            print(f'creating: {excel_output_path}')
            os.umask(0) #clears permissions
            os.makedirs(excel_output_path, mode=0o777,exist_ok=True)
    with pandas.ExcelWriter(excel_output_path/f'{case}_{scope}_DO-lt-{DO_thresh}.xlsx', mode='w') as writer:  
        H['DO_std'].to_excel(writer, sheet_name='Number_of_Days')
        VD['DO_std'].to_excel(writer, sheet_name='Volume_Days')
        PVD['DO_std'].to_excel(writer, sheet_name='Percent_Volume_Days')
        header_df.to_excel(writer, sheet_name='README')

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
