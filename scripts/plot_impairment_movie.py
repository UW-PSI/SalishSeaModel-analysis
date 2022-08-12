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

def plot_impairment_movie(shp, case, run_file, impairment=-0.2):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    impairment: default is set to -0.2
    """
    print(os.path.basename(__file__))
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
    output_directory = processed_netcdf_dir/run_type/'movies'/'impairment'
    # create output directory, if is doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
        os.makedirs(processed_netcdf_dir/run_type/'movies', mode=0o777,exist_ok=True)
        os.makedirs(processed_netcdf_dir/run_type/'movies'/'impairment',
                    mode=0o777,exist_ok=True)
    # Plot impairment for each day
    for day in range(ndays):
        output_file = output_directory/f'{case}_{run_type}_impairment3D_{day}.png'

        gdf['Impaired']=DO_diff_lt_0p2_wc[run_type][day,:]
        gdf_impaired = gdf.loc[
            ((gdf['included_i']==1) & 
            (gdf['Impaired']==True))
        ]
        gdf_good = gdf.loc[
            ((gdf['included_i']==1) & 
            (gdf['Impaired']==False))
        ]
        fig, axs = plt.subplots(1,1, figsize = (8,8))
        #~~~ Impaired (red) and Not Impaired (blue) nodes ~~~
        gdf_good.plot(ax=axs,color='blue',legend=True,
                         label='Not Impaired')
        if gdf_impaired.empty == False: # plot if there are impaired values
            gdf_impaired.plot(ax=axs,color='red',legend=True,
                             label='Impaired ($\Delta$DO<-0.2)')
        #~~~ Location map ~~~
        cx.add_basemap(axs, crs=gdf.crs,alpha=1)   
        axs.set_title(f'Impaired nodes for day {day} of 2014')
        axs.set_xticklabels('')
        axs.set_yticklabels('')
        output_file = output_directory/f'{case}_{run_type.split("_")[0]}_all_impairment_wc_{day}.png'
        plt.savefig(output_file, bbox_inches='tight', format='png')
        plt.clf() #clear figure and memory

    return

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    """
    # skip first argument, which is the file name
    args = sys.argv[1:]
    case=args[0]
    run_file=args[1]
    
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

    print(f'Calling plot_impariment_movie for: {run_file.split("/")[-2]}')
    plot_impairment_movie(shp, case, run_file)

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
