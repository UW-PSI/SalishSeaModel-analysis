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
import cmocean.cm as cm

def plot_conc_movies(shp, case, model_var, stat_type, loc, run_file):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    model_var [string]: "DOXG", "NO3", "salinity"
    """
    print(os.path.basename(__file__))
    #model_var="NO3"
    #stat_type="max"
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
    if (loc=='surface') or (loc=='bottom'):
        try: 
            with xarray.open_dataset(run_file) as ds:
                param_full=ds[[*ds][0]]
                # Sub-sample nodes (from 16012 nodes to 7494)
                param_wc=param_full[:,gdf['node_id']-1]
                # Get number of days and nodes
                [ndays,nnodes]=param_wc.shape
        except FileNotFoundError:
            print(f'File Not Found: {run_file}')
    else:
        try: 
            with xarray.open_dataset(run_file) as ds:
                param_full=ds[[*ds][0]]
                # Sub-sample nodes (from 16012 nodes to 7494)
                param=param_full[:,:,gdf['node_id']-1]
                # Apply "stat_type" across depth levels
                param_wc = getattr(np,stat_type)(param,axis=1)
                # Get number of days and nodes
                [ndays,nlevels,nnodes]=param.shape
        except FileNotFoundError:
            print(f'File Not Found: {run_file}')
    processed_netcdf_dir = pathlib.Path(
        ssm['paths']['processed_output'])/case/model_var
    output_directory = processed_netcdf_dir/'movies'/run_type/f'{model_var}_conc'
    # create output directory, if it doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
        if os.path.exists(processed_netcdf_dir/'movies'/run_type)==False:
            os.makedirs(
                processed_netcdf_dir/'movies'/run_type, 
                mode=0o777,exist_ok=True)
            os.makedirs(
                processed_netcdf_dir/'movies'/run_type/f'{model_var}_conc',
                mode=0o777,exist_ok=True)
        else:
            os.makedirs(
                processed_netcdf_dir/'movies'/run_type/f'{model_var}_conc',
                mode=0o777,exist_ok=True)

    # Re-define legend labels from, e.g. "0.00, 2.00" to "0-2"
    # NOTE: Lables are hard-coded (not ideal) and need to match 
    # values on line 113.  Don't change these values unless you 
    # also change the values on line 113!!!
    bounds = []
    if model_var=="DOXG":
        upper_bounds=[
            2, 3, 4, 5, 6, 7, np.ceil(param_wc.max().item())
        ]
        color_list=[
            'red','orange','navajowhite','beige',
            'skyblue','royalblue','midnightblue'
        ]
    # Dictionary of titles for each parameter case
    title_tag = {
        "DOXG":f"{stat_type.capitalize()} Daily Dissolved Oxygen (DO)",
        "NO3":f"{stat_type.capitalize()} Daily NO3",
        "salinity":f"{stat_type.capitalize()} Daily Salinity" 
    }
         
    # Plot threshold for each day
    for day in range(ndays):
        model_day = day + ssm['run_information']['spin_up_days'] + 1
        output_file = output_directory/f'{case}_{run_tag}_{model_var}_{stat_type}_conc_wc_{model_day}.png'

        print(f'Day {model_day} of {ndays}')
        gdf[model_var] = param_wc[day,:]
        
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
        if model_var=="DOXG":
            gdf.plot(ax=axs,
                column=model_var,
                scheme="User_Defined", 
                legend=True, 
                classification_kwds=dict(bins=upper_bounds),
                cmap=mpl.colors.ListedColormap(color_list)
            )
            # set legend to lower left corner 
            # (instead of default upper-right, which overlaps SOGNB)
            # the legend for salinity and nitrogen doesn't have the 
            # same attributes
            legend = axs.get_legend()
            legend._loc = 3 # lower-left
            legend.set_title(f'{model_var} [mg/l]')
            # # get all the legend labels
            # legend_labels = axs.get_legend().get_texts()
            for index, upper_bound in enumerate(upper_bounds):
                if index == 0:
                    lower_bound = 0
                else:
                    lower_bound = upper_bounds[index-1]

                # format the numerical legend here
                if (model_var=="DOXG") or (model_var=="salinity"):
                    bound = f'{lower_bound:.0f} - {upper_bound:.0f}'
                else:
                    bound = f'{lower_bound:.1f} - {upper_bound:.1f}'
                bounds.append(bound)
            # get all the legend labels
            legend_labels = axs.get_legend().get_texts()

            # replace the legend labels
            for bound, legend_label in zip(bounds, legend_labels):
                legend_label.set_text(bound)
        elif model_var=="salinity":
            gdf.plot(ax=axs,
                column=model_var,
                legend=True, 
                legend_kwds={'label': f'{model_var} [ppt]'},
                cmap=cm.haline,
                vmin=5,
                vmax=30
            )
        elif model_var=="NO3":
            gdf.plot(ax=axs,
                column=model_var,
                legend=True,
                legend_kwds={'label': f'{model_var} [mg/l]'},
                cmap=cm.matter,
                vmin=0,
                vmax=0.5
            )
        # remove x-, y-labels
        axs.set_xticklabels('')
        axs.set_yticklabels('')
        # add background landscape
        cx.add_basemap(axs, 
            crs=gdf.crs
        )
        
        axs.set_title(f'{title_tag[model_var]}\nDay {day} of 2014')
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
    model_var=args[1]
    stat_type=args[2]
    loc=args[3]
    run_file=args[4]
    
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

    print(f'Calling plot_conc_movie for: {run_file.split("/")[-2]}')
    plot_conc_movies(shp, case, model_var, stat_type, loc, run_file)
    
    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
