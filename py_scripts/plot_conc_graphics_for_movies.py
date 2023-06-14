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
import cmocean.cm as cm

def plot_conc_graphics(shp, case, model_var, stat_type, loc, run_file, frame="FullDomain"):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    model_var [string]: "DOXG", "NO3", "salinity"
    stat_type[string]: "mean","min","max"
    loc[string]: "surface" or "bottom"
    frame: "FullDomain" or "Region"
    """
    print(os.path.basename(__file__))
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
    print(f'run_file: {run_file}')
    print(f'run_type: {run_type}')
    print(f'run_tag: {run_tag}')
    
    # Load results from scenario for 2D case
    if (loc=='surface') or (loc=='bottom'):
        try: 
            with xarray.open_dataset(run_file) as ds:
                # there is only one variable in these files ([0]),
                # though the name changes; hence, [*ds]
                param_full=ds[[*ds][0]]
                # Sub-sample nodes (from 16012 nodes to 7494)
                param_wc=param_full[:,gdf['tce']-1]
                # Get number of days and nodes
                [ndays,nnodes]=param_wc.shape
                print(f'Opened: {run_file}')
        except FileNotFoundError:
            print(f'File Not Found: {run_file}')
    # Load results from scenario for 3D (water column) case
    else:
        try: 
            with xarray.open_dataset(run_file) as ds:
                param_full=ds[[*ds][0]]
                # Sub-sample nodes (from 16012 nodes to 7494)
                param=param_full[:,:,gdf['tce']-1]
                # Apply "stat_type" across depth levels
                param_wc = getattr(np,stat_type)(param,axis=1)
                # Get number of days and nodes
                [ndays,nlevels,nnodes]=param.shape
                print(f'Opened: {run_file}')
        except FileNotFoundError:
            print(f'File Not Found: {run_file}')
    graphics_output_dir = pathlib.Path(
        ssm['paths']['graphics'])/case/model_var
    output_directory = graphics_output_dir/'concentration'/'movies'/frame/f'{loc}'/run_type 
    print(f'Writing graphics to {output_directory}')
    # create output directory, if it doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}.  Assumed that {graphics_output_dir} exists.')
        os.umask(0) #clears permissions
        if os.path.exists(graphics_output_dir/'concentration')==False:
            os.makedirs(
                graphics_output_dir/'concentration',
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies',
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame,
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}',
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}'/run_type,
                mode=0o777,exist_ok=True)
            
        elif os.path.exists(graphics_output_dir/'concentration'/'movies')==False:
            os.makedirs(
                graphics_output_dir/'concentration'/'movies',
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame,
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}',
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}'/run_type,
                mode=0o777,exist_ok=True)
        elif os.path.exists(graphics_output_dir/'concentration'/'movies'/frame)==False:
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame,
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}',
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}'/run_type,
                mode=0o777,exist_ok=True)
        elif os.path.exists(graphics_output_dir/'concentration'/'movies'/frame/f'{loc}')==False:
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}',
                mode=0o777,exist_ok=True)
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}'/run_type,
                mode=0o777,exist_ok=True)
        else: 
            os.makedirs(
                graphics_output_dir/'concentration'/'movies'/frame/f'{loc}'/run_type,
                mode=0o777,exist_ok=True)
           
    # NOTE: Lables are hard-coded (not ideal) and need to match  
    upper_bounds={
        'DOXG': [2, 3, 4, 5, 6, 7, np.ceil(param_wc.max().item())],
        'salinity': [5, 10, 15, 20, 25, 30, 35],
        'NO3': [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6,  np.ceil(param_wc.max().item())]
    }
    
    # create legend labels
    bounds = []
    for index, upper_bound in enumerate(upper_bounds[model_var]):
        
        if index == 0:
            lower_bound = 0
        else:
            lower_bound = upper_bounds[model_var][index-1]

        # format the numerical legend here
        if (model_var=="DOXG") or (model_var=="salinity"):
            bound = f'{lower_bound:.0f} - {upper_bound:.0f}'
        else:
            bound = f'{lower_bound:.2f} - {upper_bound:.2f}'
        bounds.append(bound)
    
    color_list = {
        'DOXG': ['red','orange','navajowhite','beige','skyblue','royalblue','midnightblue'],
        'salinity': ['navy','mediumblue','cadetblue','seagreen','lightseagreen','khaki','lemonchiffon'],
        'SST': ['midnightblue','darkslateblue','darkmagenta','darkorchid',
                'palevioletred','thistle','palegoldenrod','khaki','gold','goldenrod'],
        'NO3': ['darkgoldenrod','goldenrod','darkkhaki','khaki','thistle','palevioletred','darkorchid',
                'darkmagenta','darkslateblue','midnightblue']
    }
    
    # Dictionary of titles for each parameter case
    if run_tag=='baseline':
        if (loc=='surface') or (loc=='bottom'):
            title_tag = {
                "DOXG":f"2014 Conditions\n{loc.capitalize()}, {stat_type.capitalize()} Daily Dissolved Oxygen (DO)",
                "NO3":f"2014 Conditions\n{loc.capitalize()}, {stat_type.capitalize()} Daily NO3",
                "salinity":f"2014 Conditions\n{loc.capitalize()}, {stat_type.capitalize()} Daily Salinity" 
            }
        else:
            title_tag = {
                "DOXG":f"2014 Conditions\nWater Column, {stat_type.capitalize()} Daily Dissolved Oxygen (DO)",
                "NO3":f"2014 Conditions\nWater Column, {stat_type.capitalize()} Daily NO3",
                "salinity":f"2014 Conditions\nWater Column, {stat_type.capitalize()} Daily Salinity" 
            }
    elif run_tag=='reference':
        if (loc=='surface') or (loc=='bottom'):
            title_tag = {
                "DOXG":f"Reference Scenario\n{loc.capitalize()}, {stat_type.capitalize()} Daily Dissolved Oxygen (DO)",
                "NO3":f"Reference Scenario\n{loc.capitalize()}, {stat_type.capitalize()} Daily NO3",
                "salinity":f"Reference Scenario\n{loc.capitalize()}, {stat_type.capitalize()} Daily Salinity" 
            }
        else:
            title_tag = {
                "DOXG":f"Reference Scenario\nWater Column, {stat_type.capitalize()} Daily Dissolved Oxygen (DO)",
                "NO3":f"Reference Scenario\nWater Column, {stat_type.capitalize()} Daily NO3",
                "salinity":f"Reference Scenario\nWater Column, {stat_type.capitalize()} Daily Salinity" 
            }
    else:
        if (loc=='surface') or (loc=='bottom'):
            title_tag = {
                "DOXG":f"{ssm['run_information']['run_description_short'][case][run_tag]}\n{loc.capitalize()}, {stat_type.capitalize()} Daily Dissolved Oxygen (DO)",
                "NO3":f"{ssm['run_information']['run_description_short'][case][run_tag]}\n{loc.capitalize()}, {stat_type.capitalize()} Daily NO3",
                "salinity":f"{ssm['run_information']['run_description_short'][case][run_tag]}\n{loc.capitalize()}, {stat_type.capitalize()} Daily Salinity" 
            }
        else:
            title_tag = {
                "DOXG":f"{ssm['run_information']['run_description_short'][case][run_tag]}\nWater Column, {stat_type.capitalize()} Daily Dissolved Oxygen (DO)",
                "NO3":f"{ssm['run_information']['run_description_short'][case][run_tag]}\nWater Column, {stat_type.capitalize()} Daily NO3",
                "salinity":f"{ssm['run_information']['run_description_short'][case][run_tag]}\nWater Column, {stat_type.capitalize()} Daily Salinity" 
            }

    # hard-code date period
    dti = pandas.date_range("2014-01-01", periods=367, freq="D")

    # Plot threshold for each day
    for day in range(ndays):
        model_day = day + ssm['run_information']['spin_up_days'] 
        # date to show in graphic title
        model_date = dti[model_day]
        # define output file name with model day-of-year
        output_file = output_directory/f'{case}_{run_tag}_{model_var}_{stat_type}_conc_{loc}_{model_day+1}.png'
         
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
        if frame=="Region":
            gdf.loc[(gdf['Regions']==case.capitalize())].plot(
               ax=axs,
               column=model_var,
               scheme="User_Defined",
               legend=True,
               classification_kwds=dict(bins=upper_bounds[model_var]),
               cmap=mpl.colors.ListedColormap(color_list[model_var])
            )

        else:
            gdf.plot(ax=axs,
               column=model_var,
               scheme="User_Defined", 
               legend=True, 
               classification_kwds=dict(bins=upper_bounds[model_var]),
               cmap=mpl.colors.ListedColormap(color_list[model_var])
            )
            # set graphic limits (these capture the range where DO_standard applies)
            axs.set_xlim(-1.39e7,-1.359e7)
            axs.set_ylim(5.94e6,6.3e6)
        # set legend to lower left corner 
        # (instead of default upper-right, which overlaps SOGNB)
        # the legend for salinity and nitrogen doesn't have the 
        # same attributes
        legend = axs.get_legend()
        legend._loc = 3 # lower-left
        if (model_var=='NO3') or (model_var=='DOXG'):
            legend.set_title(f'{model_var} [mg/l]')
        elif model_var=='salinity':
            legend.set_title(f'{model_var} [ppt]')
        # get all the legend labels
        legend_labels = axs.get_legend().get_texts()
        # replace the legend labels
        for bound, legend_label in zip(bounds, legend_labels):
            legend_label.set_text(bound)      
        # remove x-, y-labels
        axs.set_xticklabels('')
        axs.set_yticklabels('')
        # add background landscape
        cx.add_basemap(axs, 
            crs=gdf.crs,
            source=cx.providers.Stamen.TerrainBackground,
            alpha=1
        )
        axs.set_title(
            f"{title_tag[model_var]}\n{model_date.month_name()} {model_date.day:02d}, 2014"
        )
        plt.savefig(output_file, bbox_inches='tight', format='png')
        plt.clf() #clear figure and memory

    return

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    run_file

    frame: "FullDomain" or "Region"
    """
    # skip first argument, which is the file name
    args = sys.argv[1:]
    case=args[0]
    model_var=args[1]
    stat_type=args[2]
    loc=args[3]
    run_file=args[4]
    frame=args[5]
    
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

    print(f'Calling plot_conc_movie for: {run_file.split("/")[-2]}')
    plot_conc_graphics(shp, case, model_var, stat_type, loc, run_file, frame)
    
    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
