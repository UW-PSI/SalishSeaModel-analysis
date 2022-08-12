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

def calc_impaired_TS(shp, case, run_file, impairment=-0.2):
    """
    HEADER TO BE ADDED
    This script requires inclusion of reference case subdirectory in 
    ssm['paths']['processed_output'] as well as a specification of the reference
    case sub-directory name in the yaml file under: ssm['run_information']['reference']
    """
    
    model_var="DOXG"
    plt.rc('axes', titlesize=16)     # fontsize of the axes title

    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby(
        'Regions').count().index.to_list()
    regions.remove('Other')
 
    # Pull directory name from run_file path
    run_type = run_file.split('/')[-2]
    # Load minimum DO results from scenario
    MinDO_full={}
    MinDO={}
    try: 
        with xarray.open_dataset(run_file) as ds:
            print([*ds])
            MinDO_full[run_type]=ds[f'{model_var}_daily_min']
            # Sub-sample nodes (from 16012 nodes to 7494)
            MinDO[run_type]=MinDO_full[run_type][:,:,gdf['node_id']-1]
            print(MinDO[run_type].shape)
    except FileNotFoundError:
        print(f'File Not Found: {run_file}')
    
    # Load minimum DO results from reference case
    # Define reference run
    reference = ssm['run_information']['reference']
    base_dir = '/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/'
    reference_file = f'{base_dir}/data/{case}/DOXG/{reference}/daily_min_DOXG.nc'
    with xarray.open_dataset(reference_file) as ds:
        MinDO_full[reference]=ds[f'{model_var}_daily_min']
        # Sub-sample nodes (from 16012 nodes to 7494)
        MinDO[reference]=MinDO_full[reference][:,:,gdf['node_id']-1]
    
    # Get number of days and nodes
    [ndays,nlevels,nnodes]=MinDO[run_type].shape
    
    # Calculate volume for volume days
    volume = np.asarray(gdf.volume)
    depth_fraction = np.array(ssm['siglev_diff'])/100
    volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))
    volume3D = np.repeat(volume2D.transpose()[np.newaxis, :, :], 361, axis=0)

    # Initialize dictionaries
    DO_diff_lt_0p2={} # Boolean where DO<threshold
    DO_diff_lt_0p2_wc = {} # Boolean True where impaired at any level
 
    # Calculate impairment
    print(f'Calculating difference for {run_type}')
    # Create array of Dissolved Oxygen threshold values 
    DO_diff = MinDO[run_type] - MinDO[reference]
    # Boolean where DO_diff < -0.2 (or impairment value)
    # 361x4144 (nodes x time) or 361x10x4144
    DO_diff_lt_0p2[run_type] = DO_diff<=impairment 
    # Take max over depth level to flag node as impaired if impaired anywhere in 
    # water column
    DO_diff_lt_0p2_wc[run_type]=DO_diff_lt_0p2[run_type].max(
        axis=1, initial=0)
    processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output'])/case/model_var
    output_directory = processed_netcdf_dir/run_type/'spreadsheets'/'impairment'
    # create output directory, if is doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
        os.makedirs(
            processed_netcdf_dir/run_type/'spreadsheets', 
            mode=0o777,exist_ok=True)

    # # Initialize dictionaries
    # MinDO_full={} # Min, daily DO over all nodes
    # MinDO={} # Min, daily DO over all nodes in shapefile
    # DO_diff_lt_0p2_days={} # Number of days where DOBelowThresh = True
    # DaysImpaired={} # Sum of days across regions
    # VolumeDaysImpaired={} # Percent of volume within region where DO<threshold
    # PercentVolumeDaysImpaired={}
    # # The above summed over regions to get volume impaired per day by region
    
    DO_diff_lt_0p2={} # Boolean where DO<threshold
    volume_lt_0p2={} # 3D matrix of [0,1] where cells [are not, are] impaired
    volume_lt_0p2_TS={} # Time series of the above summed over depth and nodes
    volume_lt_0p2_TS_byRegion={} 
    percent_volume_lt_0p2_TS_byRegion={} #The above divided by region's volume
    
    # Calculate impairment
    # Create array of Dissolved Oxygen threshold values 
    DO_diff = MinDO[run_type] - MinDO[reference]
    # Boolean where DO_diff < -0.2 (or impairment value)
    #361x4144 (nodes x time) or 361x10x4144
    DO_diff_lt_0p2[run_type] = DO_diff<=impairment 
    # element-wise multiplication of two 361x10x4144 arrays
    volume_lt_0p2[run_type]=np.multiply(volume3D,DO_diff_lt_0p2[run_type])
    #add impaired volume across depth-levels and nodes
    volume_lt_0p2_TS[run_type]=volume_lt_0p2[run_type].sum(axis=1) 
    # the above summed over regions
    volume_lt_0p2_TS_byRegion[run_type]={}
    for region in regions: 
        idx = ((gdf['Regions']==region) &
                (gdf['included_i']==1))
        RegionVolume = volume[
            (gdf['Regions']==region) &
            (gdf['included_i']==1)
        ].sum()
        # time series of impaired volume in regions for each day  
        volume_lt_0p2_TS_byRegion[run_type][region] = volume_lt_0p2_TS[run_type][:,idx].sum(axis=1)
        # percent volume
        percent_volume_lt_0p2_TS_byRegion[run_type][region] = 100*(
            volume_lt_0p2_TS_byRegion[run_type][region]/RegionVolume
        )
    # repeat the above for the entire domain
    idx = (gdf['included_i']==1)
    RegionVolume = volume[
        (gdf['included_i']==1)
    ].sum()
    # time series of impaired volume in regions for each day  
    volume_lt_0p2_TS_ALL = volume_lt_0p2_TS[run_type][:,idx].sum(
                    axis=1)
    # percent volume
    percent_volume_lt_0p2_TS_byRegion[run_type]['ALL_REGIONS'] = 100*(
        volume_lt_0p2_TS_ALL/RegionVolume
    )

    # Convert to dataframe and organize information
    PercentImpaired_df = pandas.DataFrame(percent_volume_lt_0p2_TS_byRegion[run_type])
    
    return PercentImpaired_df

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    
    """
    args = sys.argv[1:]
    case=args[0]
    run_file=args[1]

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

    PercentImpaired_TS_df = calc_impaired_TS(shp, case, run_file)
        
    # make README 
    this_file = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/scripts/calc_DO_impairment_timeseries.py","calc_DO_impairment_timeseries.py")'
    run_description = '=HYPERLINK("https://uwnetid.sharepoint.com/:x:/r/sites/og_uwt_psi/_layouts/15/Doc.aspx?sourcedoc=%7B417ABADA-C061-4340-9D09-2A23A26727E6%7D&file=Municipal%20%20model%20runs%20and%20scripting%20task%20list.xlsx&action=default&mobileredirect=true&cid=b2fb77a1-5678-4b1a-b7e6-39446422cd36","Municipal model runs and scripting task list")'
    created_by = 'Rachael D. Mueller'
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_on, this_file, run_description]
    }
    header_df = pandas.DataFrame(header, index=['Created by:',
                                   'Created on:',
                                   'Created with:',
                                   'Reference:'])

    # Save to output to 
    with pandas.ExcelWriter(
        output_directory/f'{case}_wc_impaired_TS_byRegion.xlsx', mode='w') as writer:  
        PercentImpaired_TS_df.to_excel(writer, sheet_name='Percent Impaired (by volume)')
        header_df.to_excel(writer, sheet_name='README')

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
