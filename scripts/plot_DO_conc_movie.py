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

def plot_DO_conc_movie(shp, case, run_file):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    threshold: e.g. 2 mg/l, 5 mg/l or DO standard
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
    
    # Isolate run tag for image file naming
    run_tag = run_type.split("_")[0]
    if run_tag=='wqm': # for baseline and reference cases
        run_tag = run_type.split("_")[1]
    print(f'run_tag: {run_tag}')
    
    # Load minimum DO results from scenario
    try: 
        with xarray.open_dataset(run_file) as ds:
            print([*ds])
            MinDO_full=ds[f'{model_var}_daily_min']
            # Sub-sample nodes (from 16012 nodes to 7494)
            MinDO=MinDO_full[:,:,gdf['node_id']-1]
            # Take minimum across depth levels
            MinDO_wc = MinDO.min(axis=1)
    except FileNotFoundError:
        print(f'File Not Found: {run_file}')
    
    # Get number of days and nodes
    [ndays,nlevels,nnodes]=MinDO.shape
   
    processed_netcdf_dir = pathlib.Path(
        ssm['paths']['processed_output'])/case/model_var
    output_directory = processed_netcdf_dir/'movies'/run_type/'DO_conc'
    # create output directory, if it doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
        if os.path.exists(processed_netcdf_dir/'movies'/run_type)==False:
            os.makedirs(
                processed_netcdf_dir/'movies'/run_type, 
                mode=0o777,exist_ok=True)
        else:
            os.makedirs(processed_netcdf_dir/'movies'/run_type/'DO_conc',
                mode=0o777,exist_ok=True)
    
    # Plot threshold for each day
    for day in range(ndays):
        model_day = day + ssm['run_information']['spin_up_days'] + 1
        output_file = output_directory/f'{case}_{run_tag}_DO_conc_wc_{model_day}.png'

        # set all values over 7 to the maximum DO concentration
        max_idx=(MinDO_wc[day,:]>7)
        MinDO_wc[day,max_idx]=MinDO_wc.max().item()
        # set all values <2 to zero
        min_idx=(MinDO_wc[day,:]<2)
        MinDO_wc[day,min_idx]=0

        print(f'MinDO_wc[day,:] for day={model_day}:{MinDO_wc[day,:].shape}')
        gdf['DO']=MinDO_wc[day,:]
        
        # Set graphic fontsizes
        mpl.rc('font', size=10)
        # some of the following may be repetetive but can also be set 
        # relative to the font value above (eg "xx-small, x-small,small, 
        # medium, large, x-large, xx-large, larger, or smaller")
        mpl.rc('legend', fontsize=10)
        mpl.rc('axes', titlesize=14)
        mpl.rc('axes', labelsize=10)
        mpl.rc('figure', titlesize=10)
        mpl.rc('font', family='sans-serif', weight='normal', style='normal')

        fig, axs = plt.subplots(1, figsize = (8,8))
        gdf.plot(ax=axs,
            column='DO',
            scheme="User_Defined", 
            legend=True, 
            classification_kwds=dict(bins=[2,3,4,5,6,7]),
            cmap=mpl.colors.ListedColormap(
                ['red','orange','navajowhite','beige','skyblue','royalblue','midnightblue'])
        )
        # remove x-, y-labels
        axs.set_xticklabels('')
        axs.set_yticklabels('')
        # set legend to lower left corner (instead of default upper-right, which overlaps SOGNB)
        legend = axs.get_legend()
        legend._loc = 3 # lower-left
        legend.set_title('DO [mg/l]')
        # # get all the legend labels
        # legend_labels = axs.get_legend().get_texts()
        # Change legend label format from 0.00, 2.00 to 0-2
        # get and format all bounds
        bounds = []
        upper_bounds=[2,3,4,5,6,7,12.11]
        for index, upper_bound in enumerate(upper_bounds):
            if index == 0:
                lower_bound = 0
            else:
                lower_bound = upper_bounds[index-1]
            print(lower_bound, upper_bound)

            # format the numerical legend here
            bound = f'{lower_bound:.0f} - {upper_bound:.0f}'
            bounds.append(bound)
        # get all the legend labels
        legend_labels = axs.get_legend().get_texts()

        # replace the legend labels
        for bound, legend_label in zip(bounds, legend_labels):
            legend_label.set_text(bound)

        # Add land topography
        cx.add_basemap(axs, 
            crs=gdf.crs
        )
        axs.set_title(f'Minimum Daily Dissolved Oxygen (DO)\nDay {day} of 2014')
        
        plt.savefig(output_file, bbox_inches='tight', format='png')
        plt.clf() #clear figure and memory

    return

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    run_file
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

    print(f'Calling plot_DO_conc_movie for: {run_file.split("/")[-2]}')
    plot_DO_conc_movie(shp, case, run_file)
    
    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
