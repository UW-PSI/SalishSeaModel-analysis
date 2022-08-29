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

def plot_threshold_movie(shp, case, run_file, DO_thresh):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    threshold: e.g. 2 mg/l, 5 mg/l or DO standard
    """
    print(os.path.basename(__file__))
    model_var="DOXG"
    plt.rc('axes', titlesize=16)     # fontsize of the axes title

    print(f'DO_thresh: {DO_thresh}', f'data type: {type(DO_thresh)}')
    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby(
        'Regions').count().index.to_list()
    regions.remove('Other')

    # Pull directory name from run_file path
    run_type = run_file.split('/')[-2]
    
    # Isolate run tag for image file naming
    run_tag = run_type.split("_")[0]
    if run_tag=='wqm': # for baseline and reference cases
        run_tag = run_type.split("_")[1]
    print(f'run_tag: {run_tag}')
    
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

    # Get number of days and nodes
    [ndays,nlevels,nnodes]=MinDO[run_type].shape
    
    # Create array of Dissolved Oxygen threshold values
    if DO_thresh=='DO_standard':
        DO_thresh=gdf['DO_std']
        DO_thresh3D = np.ones(
            (nnodes,nlevels,ndays))*np.array(DO_thresh).reshape(nnodes,1,1)
    else:
        DO_thresh3D = np.ones((nnodes,nlevels,ndays))*int(DO_thresh)      
            
    # Calculate volume for volume days
    volume = np.asarray(gdf.volume)
    depth_fraction = np.array(ssm['siglev_diff'])/100
    # [nnodes x 1] * [1 x nlevels] -> nnodes x nlevels
    volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))
    # replicate 2D volume array over 361 days
    volume3D = np.repeat(volume2D.transpose()[np.newaxis, :, :], 361, axis=0)

    # Initialize dictionaries
    DOXGBelowThresh={} # Boolean where DO<threshold
    
    # Calculate DO below threshold
    DOXGBelowThresh[run_type] = MinDO[run_type]<=DO_thresh3D.transpose() 
    # Take max over depth level to flag node as impaired if impaired anywhere 
    # in water column
    DOXGBelowThreshDays_wc=DOXGBelowThresh[run_type].max(
        axis=1,initial=0) #361x4144 (nodes)
   
    processed_netcdf_dir = pathlib.Path(
        ssm['paths']['processed_output'])/case/model_var
    output_directory = processed_netcdf_dir/'movies'/run_type/'threshold'
    # create output directory, if is doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
        if os.path.exists(processed_netcdf_dir/'movies'/run_type)==False:
            os.makedirs(
                processed_netcdf_dir/'movies'/run_type, 
                mode=0o777,exist_ok=True)
        else:
            os.makedirs(processed_netcdf_dir/'movies'/run_type/'threshold',
                mode=0o777,exist_ok=True)
    
    # Plot threshold for each day
    for day in range(ndays):
        model_day = day + ssm['run_information']['spin_up_days'] + 1
        output_file = output_directory/f'{case}_{run_tag}_threshold_{DO_thresh}_wc_{model_day}.png'

        print(f'DOXGBelowThreshDays_wc[day,:] for day={model_day}:{DOXGBelowThreshDays_wc[day,:].shape}')
        gdf['BelowThresh']=DOXGBelowThreshDays_wc[day,:]
        gdf_belowThresh = gdf.loc[
            ((gdf['included_i']==1) & 
            (gdf['BelowThresh']==True))
        ]
        gdf_good = gdf.loc[
            ((gdf['included_i']==1) & 
             (gdf['BelowThresh']==False)&
             (gdf['Regions']!='Other'))
        ]
        fig, axs = plt.subplots(1,1, figsize = (8,8))
        #~~~ Below threshold (red) and above threshold (blue) nodes ~~~
        gdf_good.plot(ax=axs,color='blue',legend=True,
                         label='DO<={DO_thresh}[mg/l]', alpha = 0.3)
        if gdf_belowThresh.empty == False: # plot if there are impaired values
            gdf_belowThresh.plot(ax=axs,color='red',legend=True,
                             label=f'DO<{DO_thresh}[mg/l]')
        #~~~ Location map ~~~
        cx.add_basemap(axs, crs=gdf.crs,alpha=1)
        if run_tag == 'baseline':
            axs.set_title(
                f'Current conditions\nDO<{DO_thresh}[mg/l](red) for day {model_day} of 2014')
        else:
            axs.set_title(f'{run_tag}\nDO<{DO_thresh}[mg/l](red) for day {model_day} of 2014')
        
        axs.set_xticklabels('')
        axs.set_yticklabels('')
        
        plt.savefig(output_file, bbox_inches='tight', format='png')
        plt.clf() #clear figure and memory

    return

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    run_file
    DO_thresh
    """
    # skip first argument, which is the file name
    args = sys.argv[1:]
    case=args[0]
    run_file=args[1]
    DO_thresh=args[2]
    
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

    print(f'Calling plot_threshold_movie for: {run_file.split("/")[-2]}')
    plot_threshold_movie(shp, case, run_file, DO_thresh)
    
    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
