# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
import sys
import os
import yaml
import numpy as np
import pandas
import pathlib
import time
from datetime import date
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
from matplotlib.ticker import MaxNLocator
import matplotlib as mpl

def plot_5panel_noncompliant_timeseries(
    shp, case, noncompliant, excel_dir, excel_baseline_path
):
    """ 
    shp [path]: shapefile path
    case [string]: "SOG_NB" or "whidbey"
    noncompliant: -0.2 for Bounding Scenarios and -0.25 for Optimization Scenario
    """
    print(os.path.basename(__file__))
    model_var="DOXG"
    #plt.rc('axes', titlesize=16)     # fontsize of the axes title

    mpl.rc('font', size=11)
    # some of the following may be repetetive but can also be set relative to the font value above 
    #    (eg "xx-small, x-small,small, medium, large, x-large, xx-large, larger, or smaller"; see link above for details)
    mpl.rc('xtick', labelsize=12)
    mpl.rc('ytick', labelsize=12)
    mpl.rc('legend', fontsize=12)
    mpl.rc('axes', titlesize=16)
    mpl.rc('axes', labelsize=12)
    mpl.rc('figure', titlesize=16)
    mpl.rc('text', usetex=False)
    mpl.rc('font', family='sans-serif', weight='normal', style='normal')

    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby(
        'Regions').count().index.to_list()
    regions.remove('Other')
    
    # Convert noncompliant to text string to use in file name
    non_compliant_txt = str(noncompliant)
    non_compliant_txt = non_compliant_txt.replace('.','p')
    non_compliant_txt = non_compliant_txt.replace('-','m')
    
    # Select excel files in directory and omit non .xlsx items (e.g. a directory)
    print('excel_dir: ', excel_dir)
    excel_files = (file for file in os.listdir(excel_dir) if file.split('.')[-1]=='xlsx')
    
    # Pull directory name from excel_scenario_path path
    tsdf={}
    for file in excel_files:   
        print('file:',file)
        # combine directory and path name for full path
        excel_scenario_path=pathlib.Path(excel_dir,file)
        # extract run_tag from filename
        print(str(excel_scenario_path))
        run_tag = str(excel_scenario_path).split('/')[-1].split('_')[1]
        print(run_tag)
        if (run_tag !='baseline'):
            # load the scenario timeseries spreadsheets
            tsdf[run_tag]=pandas.read_excel(excel_scenario_path)
            tsdf[run_tag]=tsdf[run_tag].drop('Unnamed: 0',axis=1)
            tsdf[run_tag]['date']=np.arange(
                np.datetime64('2014-01-05'), np.datetime64('2015-01-01')
            )
            tsdf[run_tag].set_index('date')
    # load the baseline timeseries spreadsheet
    ts_base_df=pandas.read_excel(excel_baseline_path)    
    ts_base_df=ts_base_df.drop('Unnamed: 0',axis=1)
    ts_base_df['date']=np.arange(
        np.datetime64('2014-01-05'), np.datetime64('2015-01-01')
    )
    ts_base_df.set_index('date')
    # load header information
    readme=pandas.read_excel(
        excel_scenario_path, 
        sheet_name='README',
        index_col=0
    )    
    
    # create time array that reflects the removal of spin-up days
    days = np.arange(
        tsdf[run_tag].shape[0])+ssm['run_information']['spin_up_days']

    # Create output directories if/as needed
    graphics_dir = pathlib.Path(ssm['paths']['graphics'])/case
    output_directory = graphics_dir/'noncompliance'/non_compliant_txt/'5_panel'
    
    print(output_directory)
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
                graphics_dir/'noncompliance'/non_compliant_txt,
                mode=0o777,
                exist_ok=True)
            os.makedirs(
                graphics_dir/'noncompliance'/non_compliant_txt/'5_panel',
                mode=0o777,
                exist_ok=True)
        else:
            os.makedirs(
                graphics_dir/'noncompliance'/non_compliant_txt/'5_panel',
                mode=0o777,
                exist_ok=True)
  

    #~~~~  THIS SECTION NEEDS TO BE UPGRADED ~~~~~~
    #axis_dict = {
        #'1b':(0,0),
        #'1d':(1,0),
        #'1e':(2,0),
        #'2a':(3,0),
        #'2b':(4,0)
    #}

    axis_dict_1 = {
        '3b':(0,0),
        '3c':(1,0),
        '3e':(2,0),
        '3f':(3,0),
    }
    axis_dict_2 = {
        '3g':(0,0),
        '3h':(1,0),
        '3i':(2,0),
        '3l':(3,0),
        '3m':(4,0),
    }
    # ~~~~ END UPGRADE ~~~~
    # Loop through basins and plot volume non-compliant for all basins
    print(regions)
    axis_dict=axis_dict_1
    for region in regions:
        print(region)
        fig, ax = plt.subplots(nrows=4, ncols=1, figsize=(10, 6),
                       gridspec_kw={
                           'width_ratios': [1],
                           'height_ratios': [1,1,1,1],
                       'wspace': 0.25,
                       'hspace': 0.15})
        for run in [*axis_dict]:
            # get the subplot indices from dictionary
            xa=axis_dict[run][1]
            ya=axis_dict[run][0]
            print(f'[ya,xa]: [{ya},{xa}]')
            # plot results
            ax[ya].plot(
                ts_base_df['date'], 
                ts_base_df[region],
                color='black',
                label='2014 conditions'
            )
            ax[ya].plot(
                tsdf[run]['date'],
                tsdf[run][region],
                color='grey',
                ls='--',
                lw=2,
                label=f'Scenario'
            )
            # tsdf[run][region].plot(
            #     ax=ax[ya],
            #     use_index=True,
            #     kind="line",
            #     color='grey',
            #     style='--',
            #     lw=2,
            #     label=f'Scenario'
            # )
            ax[ya].grid(axis='y', color='grey',ls='dotted')
            anchored_text = AnchoredText(
                f'{run} ({region})', 
                loc='upper left',
                frameon=True,
                prop=dict(fontweight="normal",color="black")
            )
            ax[ya].add_artist(anchored_text) 
            # set the ylim to the maximum between scenario and baseline
            y_max = max(np.max(tsdf[run][region]), np.max(ts_base_df[region]))
            ax[ya].set_ylim(-2e-2*y_max, y_max)
            ax[ya].set_xlim(np.datetime64('2013-12-25'), np.datetime64('2014-12-31'))
            # set x-ticklabels to the 15th day of the month 
            ax[ya].xaxis.set_major_locator(mpl.dates.MonthLocator(bymonthday=15))
            # set x-ticklabels to the first day of the month
            ax[ya].xaxis.set_major_locator(mpl.dates.MonthLocator())
            ax[ya].xaxis.set_major_formatter(mpl.dates.DateFormatter('%m/%d'))
            if (ya!=3):
                ax[ya].set_xticklabels('')
        fig.text(0.05, 0.5, 
                 f'% Volume Non-compliant [$\Delta$ DO < {noncompliant}]', 
                 va='center', rotation='vertical'
                )
        fig.text(0.5, 0.9, 
                 region.upper(), 
                 va='center',
                 fontsize=16
            )
        ax[0].legend(bbox_to_anchor=(1, 1), loc='upper left')
        ax[2].set_xlabel('Months in 2014')

        output_file = output_directory/f'{case}_{region}_noncompliant_{non_compliant_txt}_wc_TS_a'
        print(f'saving {output_file}')
        plt.savefig(f'{output_file}.png', bbox_inches='tight', format='png')
        plt.savefig(f'{output_file}.pdf', bbox_inches='tight', format='pdf', orientation='portrait', papertype='letter')
        plt.clf() #clear figure and memory
    
    axis_dict=axis_dict_2
    for region in regions:
        print(region)
        fig, ax = plt.subplots(nrows=5, ncols=1, figsize=(10, 10),
                       gridspec_kw={
                           'width_ratios': [1],
                           'height_ratios': [1,1,1,1,1],
                       'wspace': 0.25,
                       'hspace': 0.15})
        for run in [*axis_dict]:
            # get the subplot indices from dictionary
            xa=axis_dict[run][1]
            ya=axis_dict[run][0]
            print(f'[ya,xa]: [{ya},{xa}]')
            # plot results
            ax[ya].plot(
                ts_base_df['date'],
                ts_base_df[region],
                color='black',
                label='2014 conditions'
            )
            ax[ya].plot(
                tsdf[run]['date'],
                tsdf[run][region],
                color='grey',
                ls='--',
                lw=2,
                label=f'Scenario'
            )

            ax[ya].grid(axis='y', color='grey',ls='dotted')
            anchored_text = AnchoredText(
                f'{run} ({region})',
                loc='upper left',
                frameon=True,
                prop=dict(fontweight="normal",color="black")
            )
            ax[ya].add_artist(anchored_text)
            # set the ylim to the maximum between scenario and baseline
            y_max = max(np.max(tsdf[run][region]), np.max(ts_base_df[region]))
            ax[ya].set_ylim(-2e-2*y_max, y_max)
            ax[ya].set_xlim(np.datetime64('2013-12-25'), np.datetime64('2014-12-31'))
            # set x-ticklabels to the 15th day of the month 
            ax[ya].xaxis.set_major_locator(mpl.dates.MonthLocator(bymonthday=15))
            # set x-ticklabels to the first day of the month
            ax[ya].xaxis.set_major_locator(mpl.dates.MonthLocator())
            ax[ya].xaxis.set_major_formatter(mpl.dates.DateFormatter('%m/%d'))
            if (ya!=4):
                ax[ya].set_xticklabels('')
        fig.text(0.05, 0.5,
                 f'% Volume Non-compliant [$\Delta$ DO < {noncompliant}]',
                 va='center', rotation='vertical'
                )
        fig.text(0.5, 0.9,
                 region.upper(),
                 va='center',
                 fontsize=16
            )
        ax[0].legend(bbox_to_anchor=(1, 1), loc='upper left')
        ax[4].set_xlabel('Months in 2014')

        output_file = output_directory/f'{case}_{region}_noncompliant_{non_compliant_txt}_wc_TS_b'
        print(f'saving {output_file}')
        plt.savefig(f'{output_file}.png', bbox_inches='tight', format='png')
        plt.savefig(f'{output_file}.pdf', bbox_inches='tight', format='pdf', orientation='portrait', papertype='letter')
        
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
        
    print(f'Calling plot_noncompliant_timeseries for: {file_path}')
    plot_5panel_noncompliant_timeseries(
        shp, case, float(noncompliant), 
        file_path, baseline_path)

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
