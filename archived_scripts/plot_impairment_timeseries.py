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

def plot_impairment_timeseries(
    shp, case, impairment, color, 
    excel_scenario_path, excel_baseline_path):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    impairment: -0.2 for Bounding Scenarios and -0.25 for Optimization Scenario
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

    # Convert impairment to text string to use in file name
    impaired_txt = str(impairment)
    impaired_txt = impaired_txt.replace('.','p')
    impaired_txt = impaired_txt.replace('-','m')
    
    # load the scenario and baseline timeseries spreadsheets
    tsdf=pandas.read_excel(excel_scenario_path)
    ts_base_df=pandas.read_excel(excel_baseline_path)
    tsdf=tsdf.drop('Unnamed: 0',axis=1)
    ts_base_df=ts_base_df.drop('Unnamed: 0',axis=1)
    
    # load header information
    readme=pandas.read_excel(
        excel_scenario_path, 
        sheet_name='README',
        index_col=0
    )    
    
    # create time array that reflects the removal of spin-up days
    time = np.arange(tsdf.shape[0])+ssm['run_information']['spin_up_days']

    # Create output directories if/as needed
    processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output'])/case/model_var
    output_directory = processed_netcdf_dir/'graphics'/'impairment'/impaired_txt
    # create output directory, if is doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        print(f'creating: {output_directory}')
        os.umask(0) #clears permissions
        if os.path.exists(
                processed_netcdf_dir/'graphics'/'impairment')==False:
            if os.path.exists(processed_netcdf_dir/'graphics') == False:
                os.makedirs(
                    processed_netcdf_dir/'graphics', 
                    mode=0o777,
                    exist_ok=True)
                os.makedirs(
                    processed_netcdf_dir/'graphics'/'impairment',
                    mode=0o777,
                    exist_ok=True)
                os.makedirs(
                    processed_netcdf_dir/'graphics'/'impairment'/impaired_txt,
                    mode=0o777,
                    exist_ok=True)
            else:
                os.makedirs(
                    processed_netcdf_dir/'graphics'/'impairment',
                    mode=0o777,
                    exist_ok=True)
                os.makedirs(
                    processed_netcdf_dir/'graphics'/'impairment'/impaired_txt,
                    mode=0o777,
                    exist_ok=True)
        else:
            os.makedirs(
                processed_netcdf_dir/'graphics'/'impairment'/impaired_txt,
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
    ts_base_df.plot(ax=ax,
        kind="line",
        color=color,
        legend=True
    )
    # Per Joel's request: Use black, dashed line for scenarios
    tsdf.plot(ax=ax,
        kind="line",
        color=color,
        style='--',
        lw=2,
    )
    #ax.set_xticklabel(time)
    ax.set_ylabel(f'% Volume Impaired [$\Delta$ DO < {impairment}]')
    ax.set_xlabel('Days in 2014')
    ax.set_title(f'{run_tag}(dashed line), 2014 condition (solid line)')
    ax.set_ylim(0,np.max(np.max(ts_base_df)))
    ax.set_xlim(0,365)
    ax.legend(bbox_to_anchor=(1.3, 1), loc='upper right')
    ax.grid(axis='y', color='grey')

    output_file = output_directory/f'{case}_{run_tag}_AllRegions_impairment_{impaired_txt}_wc_TS.png'
    plt.savefig(output_file, bbox_inches='tight', format='png')
    plt.clf() #clear figure and memory
    
    for region in [*tsdf]:
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 5),
                               gridspec_kw={
                                   'width_ratios': [1],
                                   'height_ratios': [1],
                               'wspace': 0.4,
                               'hspace': 0.2})
        # Per Joel's request: Use black, solid line for baseline    
        ts_base_df[region].plot(ax=ax,
            kind="line",
            color='black',
            label=f'2014 conditions',
            legend=True
        )
        # Per Joel's request: Use black, dashed line for scenarios
        tsdf[region].plot(ax=ax,
            kind="line",
            color='grey',
            lw=2,
            style='--',
            label=f'{run_tag} scenario',
            legend=True
        )
        #ax.set_xticklabel(time)
        ax.set_ylabel(f'% Volume Impaired [$\Delta$ DO < {impairment}]')
        ax.set_xlabel('Days in 2014')
        ax.set_title(f'{run_tag} [{region}]')
        ax.set_ylim(0,np.max(ts_base_df[region]))
        ax.set_xlim(0,365)
        ax.grid(axis='y', color='grey')
        output_file = output_directory/f'{case}_{run_tag}_{region}_impairment_wc_TS.png'
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
    impairment=args[0]
    case=args[1]
    file_path=args[2]
    baseline_path=args[3]
    
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
        color = [ssm['region']['colors'][region] for region in [*ssm['region']['colors']]]

    print(f'Calling plot_impariment_timeseries for: {file_path}')
    plot_impairment_timeseries(
        shp, case, float(impairment), color, 
        file_path, baseline_path)

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
