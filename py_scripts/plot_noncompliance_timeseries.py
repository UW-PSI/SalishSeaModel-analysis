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

def plot_noncompliant_timeseries(
    shp, case, noncompliant, color, 
    excel_scenario_path, excel_baseline_path,color_flag=True):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    noncompliant: -0.2 for Bounding Scenarios and -0.25 for Optimization Scenario
    color_flag: [True] use region colors specified in config file, [False] use black/white
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

    # Pull directory name from excel_scenario_path path
    run_tag = excel_scenario_path.split('/')[-1].split('_')[2]
    print(f'run_tag = {run_tag}')

    # Convert noncompliant to text string to use in file name
    noncompliant_txt = str(noncompliant)
    noncompliant_txt = noncompliant_txt.replace('.','p')
    noncompliant_txt = noncompliant_txt.replace('-','m')
    
    # load the scenario and baseline timeseries spreadsheets
    tsdf=pandas.read_excel(excel_scenario_path)
    ts_base_df=pandas.read_excel(excel_baseline_path)
    tsdf=tsdf.drop('Unnamed: 0',axis=1)
    ts_base_df=ts_base_df.drop('Unnamed: 0',axis=1)
    
    # set baseline index to dates
    ts_base_df['date']=np.arange(
        np.datetime64('2014-01-05'), np.datetime64('2015-01-01')
    )
    ts_base_df=ts_base_df.set_index('date')  
    # set scenario index to dates
    tsdf['date']=np.arange(
        np.datetime64('2014-01-05'), np.datetime64('2015-01-01')
    )
    tsdf=tsdf.set_index('date')
    
    # load header information
    readme=pandas.read_excel(
        excel_scenario_path, 
        sheet_name='README',
        index_col=0
    )    
    
    # create time array that reflects the removal of spin-up days
    time = np.arange(tsdf.shape[0])+ssm['run_information']['spin_up_days']
     

    # create time array that reflects the removal of spin-up days
    days = np.arange(
        ts_base_df.shape[0])+ssm['run_information']['spin_up_days']

    # Create output directories if/as needed
    graphics_dir = pathlib.Path(ssm['paths']['graphics'])/case
    output_directory = graphics_dir/'noncompliance'/noncompliant_txt
    # create output directory, if is doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
        if os.path.exists(graphics_dir/'noncompliance')==False:
            os.makedirs(
                graphics_dir/'noncompliance',
                mode=0o777,
                exist_ok=True)
            os.makedirs(
                graphics_dir/'noncompliance'/noncompliant_txt,
                mode=0o777,
                exist_ok=True)

    # Plot all basins
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 5),
                   gridspec_kw={
                       'width_ratios': [1],
                       'height_ratios': [1],
                   'wspace': 0.4,
                   'hspace': 0.2})
    # Per Joel's request: Use black, solid line for baseline
    ax.plot(ts_base_df,
        color='black',
        label='2014 conditions'
    )
    
    if color_flag==True:
        for region in [*tsdf]:
            ax.plot(
                tsdf[region],
                color=ssm['region']['colors'][region],
                linestyle='--',
                linewidth=2,
                label=region
            )
        output_file = output_directory/f'{case}_{run_tag}_AllRegions_noncompliant_{noncompliant_txt}_wc_TS_color'
    else:
        ax.plot(tsdf,
            color="grey",
            linestyle='--',
            linewidth=2
        )
        output_file = output_directory/f'{case}_{run_tag}_AllRegions_noncompliant_{noncompliant_txt}_wc_bw'
    
    #ax.set_xticklabel(time)
    ax.set_ylabel(f'% Volume Non-Compliant [$\Delta$ DO < {noncompliant}]')
    ax.set_xlabel('Months in 2014')
    ax.set_title(f'{run_tag}(dashed line), 2014 condition (solid line)')
    print(np.max(ts_base_df))
    print(np.max(np.max(tsdf)))
    ax.set_ylim(0,max(np.max(np.max(ts_base_df)),np.max(np.max(tsdf))))
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', color='grey')
    
    ax.set_xlim(np.datetime64('2013-12-25'), np.datetime64('2014-12-31'))
    # set x-ticklabels to the 15th day of the month 
    ax.xaxis.set_major_locator(mpl.dates.MonthLocator(bymonthday=15))
    # set x-ticklabels to the first day of the month
    ax.xaxis.set_major_locator(mpl.dates.MonthLocator())
    ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%m/%d'))

    plt.savefig(f'{output_file}.png', bbox_inches='tight', format='png')
    plt.savefig(f'{output_file}.pdf', bbox_inches='tight', format='pdf',
            orientation='portrait', papertype='letter'
        )
    plt.clf() #clear figure and memory
    
    for region in [*tsdf]:
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 5),
                               gridspec_kw={
                                   'width_ratios': [1],
                                   'height_ratios': [1],
                               'wspace': 0.4,
                               'hspace': 0.2})
        ax.plot(ts_base_df[region],
            color='black',
            label='2014 conditions'
        )
        if color_flag==True:
            ax.plot(
                tsdf[region],
                color=ssm['region']['colors'][region],
                linestyle='--',
                linewidth=2,
                label=region
            )
            output_file = output_directory/f'{case}_{run_tag}_{region}_noncompliant_wc_TS_color'
        else:
            ax.plot(tsdf,
                color="grey",
                linestyle='--',
                linewidth=2
            )
            output_file = output_directory/f'{case}_{run_tag}_{region}_noncompliant_wc_TS_bw'
        
        #ax.set_xticklabel(time)
        ax.set_ylabel(f'% Volume Non-Compliant [$\Delta$ DO < {noncompliant}]')
        ax.set_xlabel('Months in 2014')
        ax.set_title(f'{run_tag} [{region}]')
        ax.set_ylim(0,max(np.max(ts_base_df[region]),np.max(tsdf[region])))
        
        ax.set_xlim(np.datetime64('2013-12-25'), np.datetime64('2014-12-31'))
        # set x-ticklabels to the 15th day of the month 
        ax.xaxis.set_major_locator(mpl.dates.MonthLocator(bymonthday=15))
        # set x-ticklabels to the first day of the month
        ax.xaxis.set_major_locator(mpl.dates.MonthLocator())
        ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%m'))
        
        ax.grid(axis='y', color='grey')
        plt.savefig(f'{output_file}.png', bbox_inches='tight', format='png')
        plt.savefig(f'{output_file}.pdf', bbox_inches='tight', format='pdf',
            orientation='portrait', papertype='letter'
        )
        plt.clf() #clear figure and memory

    return

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    """
    # skip first argument, which is the file name
    args = sys.argv[1:]
    noncompliant=args[0]
    case=args[1]
    file_path=args[2]
    baseline_path=args[3]
    color_flag=args[4]
    
    # Start time counter
    start = time.time()

    # load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.ipynb
    # but can also be modified here (with the caveat the modifications will be 
    # over-written when the SSM_config.ipynb is run
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.yaml
    case_tag=case.split('_')[0]
    with open(f'../etc/SSM_config_{case_tag}.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
        # get shapefile path    
        shp = ssm['paths']['shapefile']
        color = [ssm['region']['colors'][region] for region in [*ssm['region']['colors']]]

    print(f'Calling plot_noncompliant_timeseries for: {file_path}')
    plot_noncompliant_timeseries(
        shp, case, float(noncompliant), color, 
        file_path, baseline_path)

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
