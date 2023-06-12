# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
import sys
import os
#sys.path.insert(1, './')
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

def calc_noncompliant(shp, case, scope, human_allowance=-0.2, non_compliant_threshold=-0.25):
    """
    HEADER TO BE ADDED
    This script requires inclusion of reference case subdirectory in 
    ssm['paths']['processed_output'] as well as a specification of the reference
    case sub-directory name in the yaml file under: ssm['run_information']['reference']
    """
    # Initialize dictionaries
    MinDO_full={} # Min, daily DO over all nodes
    MinDO={} # Min, daily DO over all nodes in shapefile
    DO_diff_lt_0p2={} # Boolean where DO<threshold
    DO_diff_lt_0p2_days={} # Number of days where DOBelowThresh = True
    DaysNonCompliant={} # Sum of days across regions
    VolumeDaysNonCompliant={} # Percent of volume within region where DO<threshold
    PercentVolumeDaysNonCompliant={}
    AreaNonCompliant={}
     
    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby(
        'Regions').count().index.to_list()
    regions.remove('Other')
    
    # Get path for model output
    model_var='DOXG'   
    processed_netcdf_dir = pathlib.Path(ssm['paths']['processed_output'])/case/model_var
    print([*ssm['run_information']['run_description_short']])
    # Get list of run sub-directories in processed netcdf directory
    dir_list = os.listdir(processed_netcdf_dir)
    print(dir_list)
    
    # Load all runs (including reference case)
    if scope=='benthic':
        print("Benthic case")
        for run_dir in dir_list: 
            try: 
                run_file=processed_netcdf_dir/run_dir/'bottom'/f'daily_min_{model_var}_bottom.nc'
                with xarray.open_dataset(run_file) as ds:
                    MinDO_full[run_dir]=ds[f'{model_var}_daily_min_bottom']
                    # Sub-sample nodes (from 16012 nodes to 7494)
                    MinDO[run_dir]=MinDO_full[run_dir][:,gdf['node_id']-1]
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nnodes]=MinDO[run_dir].shape
                # Convert DO_standard to 2D array (time, nodes)
                DO_std = np.tile(gdf.DO_std,(ndays, 1))
                unmasked = np.tile(gdf.included_i, (ndays,1))
    else: # water column (with 10 levels)
        print("Water Column")
        for run_dir in dir_list:
            print('Getting model output for: ', run_dir)
            try: 
                run_file=processed_netcdf_dir/run_dir/'wc'/f'daily_min_{model_var}_wc.nc'
                with xarray.open_dataset(run_file) as ds:
                    MinDO_full[run_dir]=ds[f'{model_var}_daily_min_wc']
                    # Sub-sample nodes (from 16012 nodes to 7494)
                    MinDO[run_dir]=MinDO_full[run_dir][:,:,gdf['node_id']-1]
            except FileNotFoundError:
                print(f'File Not Found: {run_file}')
            if run_dir == dir_list[0]:
                # Get number of days and nodes
                [ndays,nlevels,nnodes]=MinDO[run_dir].shape
                
                # Convert DO_standard to 3D array (time, depth, nodes) for Part B noncompliance calc
                DO_std = np.tile(gdf.DO_std,(ndays,nlevels,1))
                unmasked = np.tile(gdf.included_i, (ndays,nlevels,1))

    # Calculate volume for volume days
    if scope=='benthic':
        volume = np.asarray(
            gdf.volume*ssm['siglev_diff'][-1]/100) # just the bottom level
    else: # water column
        volume = np.asarray(gdf.volume)
        depth_fraction = np.array(ssm['siglev_diff'])/100
        volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))
    # Define reference run
    reference = ssm['run_information']['reference']
    dir_list.remove(reference)
    
    # Loop through all non-reference runs and calculate non_compliant_threshold
    for run_type in dir_list:
        print(f'Calculating difference for {run_type}')
        # Create array of Dissolved Oxygen threshold values 
        DO_diff = MinDO[run_type] - MinDO[reference]
        # Boolean where DO_diff < -0.2 (or non_compliant_threshold value)
        #DO_diff_lt_0p2[run_type] = DO_diff<=non_compliant_threshold #361x4144 (nodes x time) or 361x10x4144
        #DO_diff_lt_0p2[run_type] = DO_diff<=non_compliant_threshold  #361x4144 (nodes x time) or 361x10x4144
        # Part-B Noncompliance:
        # - Min DO for reference case < DO standard + human limit (0.2 mg/l) and 
        # - DO difference between case and reference is less than threshold (-0.2 or -0.25 for "rounding method")
        DO_diff_lt_0p2[run_type] = (
            (DO_diff<=non_compliant_threshold) &   #361x4144 (nodes x time) or 361x10x4144
            (MinDO[reference] < DO_std + human_allowance) &
            (unmasked==1)
        )
        # Number of days where DO < threshold = True
        if scope=='benthic':
            DO_diff_lt_0p2_days[run_type]=DO_diff_lt_0p2[run_type].sum(
                axis=0, initial=0) #4144 (nodes) or 10x4144
            VolumeDays_all=volume*DO_diff_lt_0p2_days[run_type]
        else: # water column: sum over days and take max value over depth
            # First get a count of days noncompliant for each depth level
            DO_diff_lt_0p2_days_wc=DO_diff_lt_0p2[run_type].sum(
                axis=0, initial=0)
            # Volume days: Use days noncompliant for each level  and element-wise 
            # multiplication of 10x4144 * 10x4144 matrices to get volume days by level
            VolumeDays_wc=volume2D.transpose()*DO_diff_lt_0p2_days_wc
            # Add across levels to get total VolumeDays per node
            VolumeDays_all = VolumeDays_wc.sum(axis=0)
        
        # Total number of days and percent volume days for each region
        DaysNonCompliant[run_type]={}
        AreaNonCompliant[run_type]={}
        VolumeDaysNonCompliant[run_type]={}
        PercentVolumeDaysNonCompliant[run_type]={}
        for region in regions:
            # create boolean of indices where True selects nodes of 
            # specified Region 
            idx = ((gdf['Regions']==region) &
                   (gdf['included_i']==1))            
            # Note: The max of True/False will be True and initial sets False to zero.
            # The "where" keywork specifies to only use values where idx=True,
            # which in this case I set to specify the region.
            if scope=='benthic':
                # Assign the maximum (True) of DO < threshold occurrence anywhere in region
                # then sum values over time
                DaysNonCompliant[run_type][region] = DO_diff_lt_0p2[run_type].max(
                    axis=1,where=idx,initial=0).sum().item()
            else:
                # Assign the maximum (True) of DO < threshold occurrence across depths 
                # such that 1-day of non-compliance is counted if there is one or more 
                # levels noncompliant
                DOBelowThresh_daysnodes = DO_diff_lt_0p2[run_type].max(axis=1,initial=0)
                # Assign the maximum (True) of DO < threshold occurrence 
                # anywhere in region then sum values over time
                DaysNonCompliant[run_type][region] = DOBelowThresh_daysnodes.max(
                    axis=1,where=idx,initial=0).sum().item()                
            
            # Estimate Volume Days non-compliant
            VolumeDaysNonCompliant[run_type][region]=np.array(VolumeDays_all)[
                (gdf['Regions']==region) &
                (gdf['included_i']==1)
            ].sum()
            # Estimate area of non-compliance in regions
            # I'm not sure why this next step is needed but it is.  
            # Querying the dataframe with (VolumeDays_all>0) raises a reshape error (???)
            gdf['VolumeDays_all']=VolumeDays_all  
            AreaNonCompliant[run_type][region] = 1e-6 * gdf.Area_m2.loc[
                    (gdf['Regions']==region) &
                    (gdf['included_i']==1) &
                    (gdf['VolumeDays_all']>0)
            ].sum().item()
            # get regional volume
            if scope=='benthic': # take fraction for bottom-level volume
                RegionVolume = ssm['siglev_diff'][-1]/100*volume[
                    (gdf['Regions']==region) &
                    (gdf['included_i']==1)
                ].sum()
            else: # water column
                RegionVolume = volume[
                    (gdf['Regions']==region) &
                    (gdf['included_i']==1)
                ].sum()
            PercentVolumeDaysNonCompliant[run_type][region]=100*(
                VolumeDaysNonCompliant[run_type][region]/(RegionVolume*ndays)
            )
        # Create totals across entire domain.  This includes "Other" nodes. 
        # I tested np.asarray(VolumeDays_all)[idx], where 
        # idx = (gdf['Regions']!='Other')
        # and VolumeDays_all.sum().item().  They give the same number, 
        # so I'm keeping the 29 "Other" nodes in for now
        if scope=='benthic': #(361x4771): max over nodes and sum over time
            DaysNonCompliant[run_type]['ALL_REGIONS'] = DO_diff_lt_0p2[run_type].max(
                axis=1, initial=0).sum(axis=0,initial=0).item()
        else: #(361x10x4771): max over nodes and depth and sum over time
            DaysNonCompliant[run_type]['ALL_REGIONS'] = DO_diff_lt_0p2[run_type].max(
                axis=2,initial=0).max(axis=1,initial=0).sum(axis=0,initial=0).item()
        AreaNonCompliant[run_type]['ALL_REGIONS'] = 1e-6 * gdf.Area_m2.loc[
                (gdf['included_i']==1) &
                (gdf['VolumeDays_all']>0)
        ].sum().item()
        VolumeDaysNonCompliant[run_type]['ALL_REGIONS'] = VolumeDays_all.sum().item()
        PercentVolumeDaysNonCompliant[run_type]['ALL_REGIONS'] = 100*(
            VolumeDays_all.sum().item()/(volume.sum().item()*ndays)
        )
    print(case)
    print([*ssm['run_information']['run_description_short']])
    # Create a list of column header names using the keys in "run_description_short" to map to the desired name
    # run_description_short can be used to change the run_tag if a different tag is wanted than what is used on Hyak to 
    # organize runs
    tag_list = [ssm['run_information']['run_tag'][case][tag] for tag in [*ssm['run_information']['run_description_short'][case]]]
    tag_list.remove('Reference')
    print("tag_list",tag_list)
   
    # Convert to dataframe and organize information
    DaysNonCompliant_df = pandas.DataFrame(DaysNonCompliant)
    # rename column names using dictionary (repeat this method below)
    DaysNonCompliant_df = DaysNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    # sort order of columns based on order of dictionary; otherwise, python will choose order (repeat this method below)
    DaysNonCompliant_df = DaysNonCompliant_df.reindex(columns=tag_list)
    # Area non-compliant
    AreaNonCompliant_df = pandas.DataFrame(AreaNonCompliant)
    AreaNonCompliant_df = AreaNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    AreaNonCompliant_df = AreaNonCompliant_df.reindex(columns=tag_list)
    # Percent of volume over the year in each region where DO change < threshold
    VolumeDaysNonCompliant_df = pandas.DataFrame(VolumeDaysNonCompliant)
    VolumeDaysNonCompliant_df = VolumeDaysNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    # rename columns to more readable (neccessary for SOG_NB, not so much for whidbey)
    VolumeDaysNonCompliant_df = VolumeDaysNonCompliant_df.reindex(columns=tag_list)
    # Percent of cumulative volume over the year in eash region where DO change < threshold
    PercentVolumeDaysNonCompliant_df = pandas.DataFrame(PercentVolumeDaysNonCompliant)
    PercentVolumeDaysNonCompliant_df = PercentVolumeDaysNonCompliant_df.rename(
        columns=ssm['run_information']['run_tag'][case])
    PercentVolumeDaysNonCompliant_df = PercentVolumeDaysNonCompliant_df.reindex(
        columns=tag_list
    )
    return DaysNonCompliant_df,AreaNonCompliant_df, VolumeDaysNonCompliant_df,PercentVolumeDaysNonCompliant_df

if __name__=='__main__':
    """
    HEADER information not yet added
    case: "SOG_NB" or "whidbey"
    scope: "benthic" or "wc" for water column
    """
    args = sys.argv[1:]
    case=args[0]
    non_compliant_threshold=args[1]
    scope=args[2]
    
    
    # Human Allowance.  Pre-industrial DO must be less than DO standard plus human allowance 
    # to be considered for Part B of the Dept. of Ecology's non-compliance calculation
    human_allowance = -0.2
    
    # convert non_compliant_threshold to text string to use in file name
    noncompliant_txt = non_compliant_threshold
    noncompliant_txt = noncompliant_txt.replace('.','p')
    noncompliant_txt = noncompliant_txt.replace('-','m')
    
    # Start time counter
    start = time.time()
    
    # Load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.ipynb
    # but can also be modified here (with the caveat the modifications will be 
    # over-written when the SSM_config.ipynb is run
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.yaml
    with open(f'../etc/SSM_config_{case}.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
        # get shapefile path    
        shp = ssm['paths']['shapefile']

    print('Calling calc_noncompliant')
    DaysNonCompliant_df,AreaNonCompliant_df,VolumeDays_df,PercentVolumeDays_df = calc_noncompliant(
        shp, case, scope, float(human_allowance), float(non_compliant_threshold))
        
    # make README 
    this_file = '=HYPERLINK("https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/py_scripts/calc_noncompliant.py")'
    run_description = '=HYPERLINK("https://github.com/RachaelDMueller/SalishSeaModel-analysis/tree/main/etc", "See corresponding config file")'
    non_compliant_threshold=f'{non_compliant_threshold} mg/l'
    noncompliant = f'Non Compliant in this table is defined as < {non_compliant_threshold} mg/l. A non_compliant_threshold threshold of -0.25 is described in pages 49 and 50 of the Optimization report appendix.'
    noncompliant_link = '=HYPERLINK("https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf", "Optimization Report Appendix")'
    HA=f"{human_allowance}: Pre-industrial DO must be less than DO standard plus human allowance to be considered for Part B of the Dept. of Ecology's non-compliance calculation"
    ndays = f'Number of days where DO(scenario) - DO(reference) < {non_compliant_threshold} anywhere in Region (or in benthic layer of region if benthic case)'
    vd = f'Total volume of cells in region (or benthic layer in region) that experienced DO(scenario) - DO(reference) < {non_compliant_threshold} over the course of the years'
    pvd= f'Percent of regional (or benthic) volume that experienced DO(scenario) - DO(reference) < {non_compliant_threshold} over the course of the year'

    created_by = 'Rachael D. Mueller'
    created_at = 'Puget Sound Institute'
    created_from = 'Model results produced by Su Kyong Yun (PNNL) and Rachael Mueller (PSI)'
    created_on = date.today().strftime("%B %d, %Y")
    header = {
        ' ':[created_by, created_at, created_on, this_file, 
            created_from, 
            run_description, non_compliant_threshold, noncompliant, 
            noncompliant_link, ndays, HA, vd, pvd]
    }
    header_df = pandas.DataFrame(header, index=[
        'Created by',
        'Created at',                           
        'Created on',
        'Created with',
        'Contacts',
        'Modeling by',
        'Model Run Overview',
        'Non Compliant threshold [mg/l]',
        'Non Compliant Reference',
        'Non Compliant Reference',
        'NonCompliant_Days',
        'Human Allowance [mg/l]',
        'Volume_Days [km^3 days]',
        'Percent_Volume_Days[%]'])

    # Save to output to 
    excel_output_path = pathlib.Path(ssm['paths']['processed_output'])/case/'spreadsheets'
    
    print('*************************************************************')
    print('Writing spreadsheet to: ',excel_output_path)
    print('*************************************************************')
    if os.path.exists(excel_output_path)==False:
        print(f'creating: {excel_output_path}')
        os.umask(0) #clears permissions
        os.makedirs(excel_output_path, mode=0o777,exist_ok=True)
    with pandas.ExcelWriter(
        excel_output_path/f'{case}_{scope}_noncompliant_{noncompliant_txt}.xlsx', mode='w') as writer:
        DaysNonCompliant_df.to_excel(writer, sheet_name='NonCompliant_Days')
        AreaNonCompliant_df.to_excel(writer, sheet_name='Area_NonCompliant')
        VolumeDays_df.to_excel(writer, sheet_name='Volume_Days')
        PercentVolumeDays_df.to_excel(writer, sheet_name='Percent_Volume_Days')
        header_df.to_excel(writer, sheet_name='README')

    # End time counter
    end = time.time()
    print(f'Execution time: {(end - start)/60} minutes')
