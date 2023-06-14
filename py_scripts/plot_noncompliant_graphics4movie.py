# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
import sys
import os
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

def plot_noncompliant_movie(shp, case, noncompliant, run_file, frame="FullDomain"):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    noncompliant: -0.2 for Bounding Scenarios and -0.25 for Optimization Scenario
    frame: "FullDomain" or "Region"
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
    run_type = run_file.split('/')[-3]
    # Isolate run tag for image file naming
    run_tag = run_type.split("_")[0]
    if run_tag=='wqm': # for baseline and reference cases
        run_tag = run_type.split("_")[1]

    # Convert noncompliant to text string to use in file name
    non_compliant_txt = str(noncompliant)
    non_compliant_txt = non_compliant_txt.replace('.','p')
    non_compliant_txt = non_compliant_txt.replace('-','m')
    
    # Load minimum DO results from scenario
    MinDO_full={}
    MinDO={}
    try: 
        with xarray.open_dataset(run_file) as ds:
            print([*ds])
            MinDO_full[run_type]=ds[f'{model_var}_daily_min_wc']
            # Sub-sample nodes (from 16012 nodes to 7494)
            MinDO[run_type]=MinDO_full[run_type][:,:,gdf['node_id']-1]
            print(MinDO[run_type].shape)
    except FileNotFoundError:
        print(f'File Not Found: {run_file}')

    # Load minimum DO results from reference case
    reference = ssm['run_information']['reference']
    base_dir = '/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/'
    reference_file = f'{base_dir}/data/{case}/DOXG/{reference}/wc/daily_min_DOXG_wc.nc'
    with xarray.open_dataset(reference_file) as ds:
        MinDO_full[reference]=ds[f'{model_var}_daily_min_wc']
        # Sub-sample nodes (from 16012 nodes to 7494)
        MinDO[reference]=MinDO_full[reference][:,:,gdf['node_id']-1]
    
    # Get number of days and nodes
    [ndays,nlevels,nnodes]=MinDO[run_type].shape

    # Convert DO_standard to 3D array (time, depth, nodes) for Part B noncompliance calc
    DO_std = np.tile(gdf.DO_std,(ndays,nlevels,1))

    # Calculate volume for volume days
    volume = np.asarray(gdf.volume)
    depth_fraction = np.array(ssm['siglev_diff'])/100
    volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))
    volume3D = np.repeat(volume2D.transpose()[np.newaxis, :, :], 361, axis=0)

    # Initialize dictionaries
    DO_diff_lt_0p2={} # Boolean where DO<threshold
    DO_diff_lt_0p2_wc = {} # Boolean True where non_compliant at any level
    
    # Calculate noncompliant
    print(f'Calculating difference for {run_type}')
    # Create array of Dissolved Oxygen threshold values 
    DO_diff = MinDO[run_type] - MinDO[reference]
    # Boolean where DO_diff < -0.2 (or noncompliant value)
    # 361x4144 (nodes x time) or 361x10x4144
    DO_diff_lt_0p2[run_type] = (
       (DO_diff<=noncompliant) &   #361x4144 (nodes x time) or 361x10x4144
       (MinDO[reference] < DO_std + 0.2)
    )
    # Take max over depth level to flag node as non_compliant if non_compliant anywhere in 
    # water column
    DO_diff_lt_0p2_wc[run_type]=DO_diff_lt_0p2[run_type].max(
        axis=1, initial=0)
    processed_netcdf_dir = pathlib.Path(ssm['paths']['graphics'])/case
    output_directory = processed_netcdf_dir/'noncompliance'/non_compliant_txt/'movies'/frame/run_type
    # create output directory, if is doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
       
        if os.path.exists(processed_netcdf_dir)==False: 
            os.makedirs( 
                processed_netcdf_dir,  
                mode=0o777, 
                exist_ok=True) 
            os.makedirs( 
                processed_netcdf_dir/'noncompliance',  
                mode=0o777, 
                exist_ok=True) 
            os.makedirs(
                processed_netcdf_dir/'noncompliance'/non_compliant_txt, 
                mode=0o777,
                exist_ok=True)
            os.makedirs(
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/frame, 
                mode=0o777,
                exist_ok=True)
            os.makedirs(
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/'movies'/frame/run_type, 
                mode=0o777,
                exist_ok=True)
            
        elif os.path.exists(processed_netcdf_dir/'noncompliance')==False:
            os.makedirs(
                processed_netcdf_dir/'noncompliance', 
                mode=0o777,
                exist_ok=True)
            os.makedirs(
                processed_netcdf_dir/'noncompliance'/non_compliant_txt, 
                mode=0o777,
                exist_ok=True)
            os.makedirs(
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/frame, 
                mode=0o777,
                exist_ok=True)
            os.makedirs(
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/'movies'/frame/run_type, 
                mode=0o777,
                exist_ok=True)

        elif os.path.exists(processed_netcdf_dir/'noncompliance'/non_compliant_txt)==False: 
            os.makedirs( 
                processed_netcdf_dir/'noncompliance'/non_compliant_txt,  
                mode=0o777, 
                exist_ok=True) 
            os.makedirs( 
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/frame,  
                mode=0o777, 
                exist_ok=True) 
            os.makedirs( 
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/'movies'/frame/run_type,  
                mode=0o777, 
                exist_ok=True)    
        elif os.path.exists(processed_netcdf_dir/'noncompliance'/non_compliant_txt/frame)==False: 
            os.makedirs( 
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/frame,  
                mode=0o777, 
                exist_ok=True) 
            os.makedirs( 
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/'movies'/frame/run_type,  
                mode=0o777, 
                exist_ok=True)  
        else: 
            os.makedirs( 
                processed_netcdf_dir/'noncompliance'/non_compliant_txt/'movies'/frame/run_type,  
                mode=0o777, 
                exist_ok=True)  
    # Create a time array for title
    # This is a quick-and-easy solution that hard-codes the date. 
    # It needs to be modified to make for a more general application
    dti = pandas.date_range("2014-01-01", periods=367, freq="D")
    
    # Plot noncompliant for each day
    for day in range(ndays):
        model_day = day + ssm['run_information']['spin_up_days'] 
        model_date = dti[model_day]

        gdf['noncompliant']=DO_diff_lt_0p2_wc[run_type][day,:]
        if frame=="FullDomain":
            gdf_non_compliant = gdf.loc[
                ((gdf['included_i']==1) & 
                (gdf['noncompliant']==True))
            ]
            gdf_good = gdf.loc[
                ((gdf['included_i']==1) & 
                (gdf['noncompliant']==False) & 
                (gdf['Regions']!='Other'))
            ]
        else:
            if case=='SOG':
                gdf_non_compliant = gdf.loc[
                    ((gdf['included_i']==1) & 
                    (gdf['noncompliant']==True) &
                    (gdf['Regions']=='SOG_Bellingham'))
                ]
                gdf_good = gdf.loc[
                    ((gdf['included_i']==1) & 
                    (gdf['noncompliant']==False) & 
                    (gdf['Regions']=='SOG_Bellingham')
                     )
                ]
            elif case=='South':
                gdf_non_compliant = gdf.loc[
                    ((gdf['included_i']==1) & 
                    (gdf['noncompliant']==True) &
                    (gdf['Regions']=='South_Sound'))
                    ]
                gdf_good = gdf.loc[
                    ((gdf['included_i']==1) & 
                    (gdf['noncompliant']==False) & 
                    (gdf['Regions']=='South_Sound')
                     )
                ]
            else:
                gdf_non_compliant = gdf.loc[
                    ((gdf['included_i']==1) & 
                    (gdf['noncompliant']==True) &
                    (gdf['Regions']==case.capitalize()))
                ]
                gdf_good = gdf.loc[
                    ((gdf['included_i']==1) & 
                    (gdf['noncompliant']==False) & 
                    (gdf['Regions']==case.capitalize())
                     )
                ]
        fig, axs = plt.subplots(1,1, figsize = (8,8))
        #~~~ noncompliant (red) and Not noncompliant (blue) nodes ~~~
        gdf_good.plot(ax=axs,color='blue',legend=True,
                         label='Not noncompliant', alpha=0.3)
        if gdf_non_compliant.empty == False: # plot if there are non_compliant values
            gdf_non_compliant.plot(ax=axs,color='red',legend=True,
                             label='noncompliant ($\Delta$DO < {noncompliant})')
        #~~~ Location map ~~~
        cx.add_basemap(axs, crs=gdf.crs, source=cx.providers.Stamen.TerrainBackground, alpha=1) 
        if run_tag=='baseline':
           axs.set_title(f"{ssm['run_information']['run_description_short'][case]['wqm_baseline']}\n non-compliant nodes for {model_date.month_name()} {model_date.day:02d}, 2014")
        elif run_tag=='reference':
           axs.set_title(f"{ssm['run_information']['run_description_short'][case]['wqm_reference']}\n non-compliant nodes for {model_date.month_name()} {model_date.day:02d}, 2014")
        else:
           axs.set_title(f"{ssm['run_information']['run_description_short'][case][run_tag]}\n non-compliant nodes for {model_date.month_name()} {model_date.day:02d}, 2014")

        axs.set_xticklabels('')
        axs.set_yticklabels('')
        output_file = output_directory/f'{case}_{run_tag}_all_noncompliant_wc_{model_day+1}.png'
        plt.savefig(output_file, bbox_inches='tight', format='png')
        plt.clf() #clear figure and memory

    return

if __name__=='__main__':
    """
    HEADER information not yet added
    case: 'SOG', 'Whidbey', 'Main', 'South', 'Hood', or 'SJF'
    frame: 'FullDomain' or 'Region'
    """
    # skip first argument, which is the file name
    args = sys.argv[1:]
    noncompliant=args[0]
    case=args[1]
    run_file=args[2]
    frame=args[3]
    
    # Start time counter
    start = time.time()

    # load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.ipynb
    # but can also be modified here (with the caveat the modifications will be 
    # over-written when the SSM_config.ipynb is run
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.yaml
    with open(f'../etc/SSM_config_{case}.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
        # get shapefile path    
        shp = ssm['paths']['shapefile']

    print(f'Calling plot_noncompliant_movie for: {run_file.split("/")[-2]}')
    plot_noncompliant_movie(shp, case, float(noncompliant), run_file, frame)

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
