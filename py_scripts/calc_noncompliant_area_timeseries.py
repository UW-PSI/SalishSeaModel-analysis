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

def calc_noncompliant_TS(shp, case, noncompliance, human_allowance, model_var, run_file):
    """
    HEADER TO BE ADDED
    This script requires inclusion of reference case subdirectory in 
    ssm['paths']['processed_output'] as well as a specification of the reference
    case sub-directory name in the yaml file under: ssm['run_information']['reference']
    """
    
    #model_var="DOXG"
    plt.rc('axes', titlesize=16)     # fontsize of the axes title
    
    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby(
        'Regions').count().index.to_list()
    regions.remove('Other')
    print(regions)
 
    # Pull directory name from run_file path
    run_type = run_file.split('/')[-3]
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
    # Define reference run
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
    unmasked = np.tile(gdf.included_i, (ndays,nlevels,1))
    # Calculate volume for volume days
    #area = np.asarray(gdf.Area_m2)
    # depth_fraction = np.array(ssm['siglev_diff'])/100
    # volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))
    # volume3D = np.repeat(volume2D.transpose()[np.newaxis, :, :], 361, axis=0)

    # Initialize dictionaries
    DO_diff_lt_0p2={} # Boolean where DO<threshold
    DO_diff_lt_0p2_wc = {} # Boolean True where noncompliant at any level
 
    # Calculate noncompliance
    print(f'Calculating difference for {run_type}')
    # Create array of Dissolved Oxygen threshold values 
    DO_diff = MinDO[run_type] - MinDO[reference]
    # Boolean where DO_diff < -0.2 (or noncompliance value)
    # 361x4144 (nodes x time) or 361x10x4144
    #DO_diff_lt_0p2[run_type] = DO_diff<=noncompliance 
    DO_diff_lt_0p2[run_type] = (
            (DO_diff<=noncompliance) &   #361x4144 (nodes x time) or 361x10x4144
            (MinDO[reference] < DO_std + human_allowance)&
            (unmasked==1)
        )
    # Take max over depth level to flag node as noncompliant if noncompliant anywhere in 
    # water column
    DO_diff_lt_0p2_wc[run_type]=DO_diff_lt_0p2[run_type].max(
        axis=1, initial=0)
    # # Initialize dictionaries
    DO_diff_lt_0p2={} # Boolean where DO<threshold
    area_lt_0p2_TS={} # Time series with area at noncompliant nodes
 
    # Calculate noncompliance
    # Create array of Dissolved Oxygen threshold values 
    DO_diff = MinDO[run_type] - MinDO[reference]
    # Boolean where DO_diff < -0.2 (or noncompliance value)
    #361x4144 (nodes x time) or 361x10x4144
    DO_diff_lt_0p2[run_type] = DO_diff<=noncompliance 
    # element-wise multiplication of two 361x10x4144 arrays
    area = np.asarray(gdf.Area_m2)
    area2D = np.repeat(area[np.newaxis, :], 361, axis=0)
    area_lt_0p2_TS[run_type]=np.multiply(area2D, DO_diff_lt_0p2[run_type].max(axis=1))
    # percent of region's volume that is noncompliant
    total_area_noncompliant_byRegion={}
    total_area_noncompliant_byRegion[run_type]={}
    for region in regions: 
        idx = ((gdf['Regions']==region) &
                (gdf['included_i']==1))
        RegionArea = area[
            (gdf['Regions']==region) &
            (gdf['included_i']==1)
        ].sum()
        
        # time series of noncompliant volume in regions for each day  
        total_area_noncompliant_byRegion[run_type][region] = area_lt_0p2_TS[run_type][:,idx].sum(axis=1)
        
    # repeat the above for the entire domain
    idx = (gdf['included_i']==1)
    RegionArea = area[
        (gdf['included_i']==1)
    ].sum()
    # time series of noncompliant volume in regions for each day  
    total_area_noncompliant_ALL = area_lt_0p2_TS[run_type][:,idx].sum(
                    axis=1)
    # Convert to dataframe and organize information
    TotalAreaNoncompliant_df = pandas.DataFrame(total_area_noncompliant_byRegion[run_type])
    
    return TotalAreaNoncompliant_df, output_directory

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    noncompliance: -0.2 in Bounding Scenarios and -0.25 in Optimization
    """
    args = sys.argv[1:]
    noncompliance=args[0]
    case=args[1]
    run_file=args[2]
    model_var="DOXG"
    
    # Human Allowance.  Pre-industrial DO must be less than DO standard plus human allowance 
    # to be considered for Part B of the Dept. of Ecology's non-compliance calculation
    human_allowance = -0.2

    # convert noncompliance to text string to use in file name
    noncompliant_txt = noncompliance
    noncompliant_txt = noncompliant_txt.replace('.','p')
    noncompliant_txt = noncompliant_txt.replace('-','m')

    # Start time counter
    start = time.time()
    
    # Load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config_*.ipynb
    with open(f'../etc/SSM_config_{case}.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
        # get shapefile path    
        shp = ssm['paths']['shapefile']

    processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output'])/case
    output_directory = processed_netcdf_dir/'spreadsheets'#/'noncompliance'/noncompliant_txt
    # create output directory, if is doesn't already exist 
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_directory)==False:
        if os.path.exists(processed_netcdf_dir/'spreadsheets')==False:
            os.umask(0) #clears permissions
            os.makedirs(
                processed_netcdf_dir/'spreadsheets', 
                mode=0o777,exist_ok=True)


    TotalAreaNoncompliant_df,output_directory = calc_noncompliant_TS(
            shp, case, float(noncompliance), float(human_allowance), model_var, run_file
            )
    
    # Pull directory name from run_file path
    run_type = run_file.split('/')[-3]
    
    # Create a run scenario tag-name for file naming
#    run_tag = run_type.split("_")[0]
#     if run_tag=='wqm': # for baseline and reference cases
#         run_tag = run_type.split("_")[1]
    print(run_file.split('/')[-3])
    if run_type.split("_")[0] != 'wqm':
        run_tag = run_type.split("_")[0]
    else:
        run_tag = run_type
    
    # make README 
    this_file = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/scripts/calc_DO_noncompliance_timeseries.py","calc_DO_noncompliant_area_timeseries.py")'
    run_description = '=HYPERLINK("https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/docs/supporting/KingCounty_Model_Runs.xlsx","KingCounty_Model_Runs.xlsx")'
    run_name_on_hyak=f'This run is stored on Hyak under the tag {run_tag}'
    noncompliance_value=f'{noncompliance} mg/l'
    noncompliant = f'Non-compliance in this table is defined as < {noncompliance} mg/l. An noncompliance threshold of -0.25 is described in pages 49 and 50 of the Optimization report appendix.'
    noncompliant_link = '=HYPERLINK("https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf", "Optimization Report Appendix")'
    HA=f"{human_allowance}: Pre-industrial DO must be less than DO standard plus human allowance to be considered for Part B of the Dept. of Ecology's non-compliance calculation"
    created_by = 'Rachael D. Mueller'
    created_at = 'Puget Sound Institute'
    created_from = 'Model results produced by Su Kyong Yun (PNNL) and Rachael D. Mueller (PSI)'
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_at, created_on, this_file,
            created_from,
            run_description, run_name_on_hyak, noncompliance_value, HA, noncompliant,
            noncompliant_link]
    }
    header_df = pandas.DataFrame(header, index=[
        'Created by',
        'Created at',
        'Created on',
        'Created with',
        'Modeling by',
        'Model Run Overview',
        'Hyak name',
        'Non-compliant threshold [mg/l]',
        'Human Allowance [mg/l]',
        'Non-compliant Reference',
        'Non-compliant Reference'])

    # Save to file
    # map file name from Hyak run-name to reference run-name
    print(run_tag)
    if run_tag == "wqm_baseline":
        print('here')
        output_file = f"{case}_baseline_wc_noncompliant_AREA_{noncompliant_txt}_TS_byRegion.xlsx"
    else:    
        output_file = f"{case}_{ssm['run_information']['run_tag'][case][run_tag]}_wc_noncompliant_AREA_{noncompliant_txt}_TS_byRegion.xlsx"
    with pandas.ExcelWriter(output_directory/output_file, mode='w') as writer:  
        TotalAreaNoncompliant_df.to_excel(writer, sheet_name='Total Area Non-compliant')
        header_df.to_excel(writer, sheet_name='README')

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
