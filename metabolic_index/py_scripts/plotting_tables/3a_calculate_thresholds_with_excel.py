#!/usr/bin/env python
"""
Calculate Thresholds with Excel Export
Cells 35-40 from original notebook
"""


# ============================================================================
# ## Threshold function with excel export(inside function)
# ============================================================================

# ==============================================================================
# BLOCK: WATER COLUMN ANALYSIS (3D) - thresholding from source files function and excel export (embedded)
# ==============================================================================

# ==============================================================================
# EMBEDDED CALC_DO_BELOW_THRESH FUNCTION - ADAPTED FOR 2025 STRUCTURE
# SM Modified to use direct source data mapping approach instead of file loading
# ==============================================================================
def calc_DO_below_thresh(case, DO_thresh, shp, scope, ssm_config, ssm_input_datasets):  #Accept ssm_input_datasets as parameter instead of loading files
    """ 
    calc_DO_below_thresh function - data passed as parameter
    
    Parameters:
    case [string]: "SOG_NB" or "whidbey"
    DO_thresh [1D or int]: "DO_standard" or integer value
    shp [path]: shapefile path
    scope [string]: "benthic" or "wc" (for water column)
    ssm_config [dict]: SSM configuration dictionary
    ssm_input_datasets [dict]: Pre-loaded data dictionary with existing/reference data
    """
    
    # ********************************************************************
    # SECTION 1: INITIALIZATION
    # ********************************************************************
    
    # Use passed dataset directly
    MinDO_full = ssm_input_datasets  # Use passed dataset directly, keep internal variable name for minimal code changes
    
    # Initialize dictionaries
    MinDO = {}
    DOXGBelowThresh = {}  # Boolean where DOXG<threshold
    DOXGBelowThreshDays = {}  # Number of days where DOXGBelowThresh = True
    DaysDOXGBelowThresh = {}  # Sum of days across regions
    VolumeDays = {}  # Percent of volume within region where DO<threshold
    PercentVolumeDays = {}
    
    # Define dimension sizes and load shapefile
    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={'region_inf': 'Regions'})
    regions = gdf[['node_id', 'Regions']].groupby('Regions').count().index.to_list()
    regions.remove('Other')  # note:comment this line if you need to keep other
    
    # ********************************************************************
    # SECTION 2: DATA LOADING (SIMPLE DIRECT MAPPING APPROACH)
    # ********************************************************************
    #Use pre-loaded data from global EG MinDO_full dictionary instead of file loading approach
    print("Using pre-loaded data from mapping cell")
    
    # Check if data is available - ensures mapping cell was executed before function call
    if not MinDO_full:  # Validate that data mapping cell populated the global dictionary before proceeding
        raise ValueError("MinDO_full dictionary is empty. Run the data mapping cell first.")
    
    print(f"Found data for scenarios: {list(MinDO_full.keys())}")  # Display available scenario names for debugging
    
    # Get list of run directories from loaded data keys
    dir_list = list(MinDO_full.keys())
    
    # Subset to shapefile nodes for each scenario - extract only nodes present in shapefile from full model grid
    for run_dir in dir_list:  # Iterate through all scenario names (keys) in the pre-loaded data dictionary
        if scope == 'benthic':
            MinDO[run_dir] = MinDO_full[run_dir][:, gdf['node_id'].values-1]  #added .values to convert pandas Series to numpy array for proper indexing
        else:  # water column
            MinDO[run_dir] = MinDO_full[run_dir][:, :, gdf['node_id'].values-1]  #added .values to convert pandas Series to numpy array for proper indexing
    
    # Set dimensions from loaded data
    first_key = list(MinDO.keys())[0]
    if scope == 'benthic':
        ndays, nnodes = MinDO[first_key].shape
    else:  # water column
        ndays, nlevels, nnodes = MinDO[first_key].shape
    
    # ********************************************************************
    # SECTION 3: THRESHOLD ARRAY CREATION
    # ********************************************************************
    
    # Save original threshold name for filename BEFORE conversion
    thresh_filename = str(DO_thresh)  # Convert whatever it is to string
    
    # Create array of Dissolved Oxygen threshold values
    if DO_thresh == 'DO_standard':
        DO_thresh = gdf['DO_std']
        if scope == 'benthic':
            # create array of DO_threshold values
            # (7494,361) x (7494,1) => element-wise multiplication
            DO_thresh2D = np.ones((nnodes, ndays)) * np.array(DO_thresh).reshape(nnodes, 1)
        else:
            DO_thresh3D = np.ones((nnodes, nlevels, ndays)) * np.array(DO_thresh).reshape(nnodes, 1, 1)
    else:
        print("***", DO_thresh, type(DO_thresh))
        if scope == 'benthic':
            DO_thresh2D = np.ones((nnodes, ndays)) * int(DO_thresh)
        else:
            DO_thresh3D = np.ones((nnodes, nlevels, ndays)) * int(DO_thresh)
    
    # ********************************************************************
    # SECTION 4: VOLUME CALCULATIONS
    # ********************************************************************
    
    # Calculate volume for volume days
    if scope == 'benthic':  # just the bottom level
        volume = np.asarray(gdf.volume * ssm_config['siglev_diff'][-1] / 100)
    else:  # water column
        volume = np.asarray(gdf.volume)
        depth_fraction = np.array(ssm_config['siglev_diff']) / 100
        volume2D = np.dot(volume.reshape(nnodes, 1), depth_fraction.reshape(1, nlevels))
    
    # ********************************************************************
    # SECTION 5: THRESHOLD ANALYSIS CALCULATIONS
    # ********************************************************************
    
    # Determine DOXGBelowThresh days
    for run_type in dir_list:
        print(f'Calculating threshold analysis for {run_type}')
        # Boolean where DOXG<threshold
        if scope == 'benthic':
            # 361x4144 (nodes x time)
            DOXGBelowThresh[run_type] = MinDO[run_type] <= DO_thresh2D.transpose()
            # Number of days where DOXGBelowThresh = True
            DOXGBelowThreshDays[run_type] = DOXGBelowThresh[run_type].sum(axis=0, initial=0)
            # Volume days
            VolumeDays_all = volume * DOXGBelowThreshDays[run_type]
        else:  # water column
            # 361x10x4144 (nodes x depth x time)
            DOXGBelowThresh[run_type] = MinDO[run_type] <= DO_thresh3D.transpose()
            # First get a count of days below threshold for each depth level
            DOXGBelowThreshDays_wc = DOXGBelowThresh[run_type].sum(axis=0, initial=0)  # 10x4144 (nodes)
            # Volume days: Use days impaired for each level and element-wise 
            # multiplication of 10x4144 * 10x4144 matrices to get volume days by level 
            VolumeDays_wc = volume2D.transpose() * DOXGBelowThreshDays_wc
            # Add across levels to get total VolumeDays per node
            VolumeDays_all = VolumeDays_wc.sum(axis=0)
        
        # ********************************************************************
        # SECTION 6: REGIONAL ANALYSIS
        # ********************************************************************
        
        # Total number of days and percent volume days for each region
        DaysDOXGBelowThresh[run_type] = {}
        VolumeDays[run_type] = {}
        PercentVolumeDays[run_type] = {}
        for region in regions:
            # create boolean of indices where True selects nodes of specified Region 
            idx_pandas = ((gdf['Regions'] == region) & (gdf['included_i'] == 1))
            idx = np.asarray(idx_pandas, dtype=bool)  #SM Convert mixed pandas/xarray to numpy bool array
            
            # Note: The max of True/False will be True and initial sets False to zero.
            # The "where" keyword specifies to only use values where idx=True,
            # which in this case I set to specify the region.
            if scope == 'benthic':
                # Assign the maximum (True) of DO < threshold occurrence across region
                DaysDOXGBelowThresh[run_type][region] = DOXGBelowThresh[run_type].max(
                    axis=1, where=idx, initial=0).sum().item()
            else:
                # Assign the maximum (True) of DO < threshold occurrence across depths
                # Take max over depth to assign True if DO < threshold in one or more levels
                DOXGBelowThresh_daysnodes = DOXGBelowThresh[run_type].max(axis=1, initial=0)
                # Assign the maximum (True) if DO < threshold occurrence across region
                # then add values over time to get days < threshold
                DaysDOXGBelowThresh[run_type][region] = DOXGBelowThresh_daysnodes.max(
                    axis=1, where=idx, initial=0).sum().item()
            
            VolumeDays[run_type][region] = np.array(VolumeDays_all)[
                (gdf['Regions'] == region) & (gdf['included_i'] == 1)
            ].sum()
            
            # get regional volume
            if scope == 'benthic':  # take fraction for bottom-level volume
                RegionVolume = ssm_config['siglev_diff'][-1] / 100 * volume[
                    (gdf['Regions'] == region) & (gdf['included_i'] == 1)
                ].sum()
            else:  # water column
                RegionVolume = volume[
                    (gdf['Regions'] == region) & (gdf['included_i'] == 1)
                ].sum()
            
            PercentVolumeDays[run_type][region] = 100 * (
                VolumeDays[run_type][region] / (RegionVolume * ndays)
            )
        
        # Add sum across all region to the dataframe
        #DAYS
        #SM- Add inclusion filter because ALL_REGIONS was counting excluded nodes that individual regions ignore
        #DEBUG NOTE: For <2 mg/L threshold, ALL_REGIONS = 186 days (matching Hood Canal's maximum) because Hood Canal's hypoxic periods encompass all other regions' events - correct logical union, not arithmetic sum.
        if scope == 'benthic':
            #ALL_REGIONS needs to be calculated separately as it's not in the "regions" list, calculation finds all days where any included node was below threshold
            idx_all_included = (gdf['included_i'] == 1).values #create boolean mask selecting only nodes that are included in analysis to match regional filtering logic
            DaysDOXGBelowThresh[run_type]['ALL_REGIONS'] = DOXGBelowThresh[run_type].max(
                axis=1, where=idx_all_included, initial=0).sum(axis=0, initial=0).item() #axis=1 takes maximum boolean value across all included nodes for each day to find if any node was below threshold, where= applies inclusion filter to only consider included nodes, initial=0 returns False when no included nodes found, sum() counts number of days with True values meaning days with threshold exceedance
        else:
            DOXGBelowThresh_daysnodes = DOXGBelowThresh[run_type].max(axis=1, initial=0) #axis=1 takes maximum boolean value over all depth levels for each day/node combination to find if any depth at that node was below threshold, initial=0 returns False when no depths found
            #ALL_REGIONS needs to be calculated separately as it's not in the "regions" list, calculation finds all days where any included node at any depth was below threshold  
            idx_all_included = (gdf['included_i'] == 1).values #create boolean mask selecting only nodes that are included in analysis to match regional filtering logic
            DaysDOXGBelowThresh[run_type]['ALL_REGIONS'] = DOXGBelowThresh_daysnodes.max(
                axis=1, where=idx_all_included, initial=0).sum().item() #axis=1 takes maximum boolean value across all included nodes for each day to find if any included node was below threshold, where= applies inclusion filter to only consider included nodes, initial=0 returns False when no included nodes found, sum() counts number of days with True values meaning days with threshold exceedance
        # Volume and % volume:
        VolumeDays[run_type]['ALL_REGIONS'] = VolumeDays_all.sum().item()
        PercentVolumeDays[run_type]['ALL_REGIONS'] = 100 * (
            VolumeDays_all.sum().item() / (volume.sum().item() * ndays)
        )
    
    # ********************************************************************
    # SECTION 7: DATAFRAME CREATION AND RETURN
    # ********************************************************************
    
    # Create a list of column header names
    tag_list = [ssm_config['run_information']['run_tag'][case][tag] for tag in [*ssm_config['run_information']['run_tag'][case]]]
    # Keep all scenarios including Reference for threshold analysis
    
    # Convert to dataframe and organize information
    DaysDOXGBelowThresh_df = pandas.DataFrame(DaysDOXGBelowThresh)
    DaysDOXGBelowThresh_df = DaysDOXGBelowThresh_df.rename(
        columns=ssm_config['run_information']['run_tag'][case])
    DaysDOXGBelowThresh_df = DaysDOXGBelowThresh_df.reindex(columns=tag_list)
    
    # Percent of volume over the year in each region where DOXG change < threshold
    VolumeDays_df = pandas.DataFrame(VolumeDays)
    VolumeDays_df = VolumeDays_df.rename(
        columns=ssm_config['run_information']['run_tag'][case])
    VolumeDays_df = VolumeDays_df.reindex(columns=tag_list)
    
    # Percent of cumulative volume over the year in each region where DOXG change < threshold
    PercentVolumeDays_df = pandas.DataFrame(PercentVolumeDays)
    PercentVolumeDays_df = PercentVolumeDays_df.rename(
        columns=ssm_config['run_information']['run_tag'][case])
    PercentVolumeDays_df = PercentVolumeDays_df.reindex(columns=tag_list)
    
    # ==============================================================================
    # EXCEL EXPORT - MOVED INSIDE FUNCTION HERE
    # ==============================================================================
    
    # Create Excel output path for threshold analysis
    #excel_output_path = excel_output_path # defined in initialization section
    
    # Create README information for threshold analysis
    this_file = '=HYPERLINK(\"https://github.com/UW-PSI/SalishSeaModel-analysis/\")'
    run_description = '=HYPERLINK(\"https://github.com/UW-PSI/SalishSeaModel-analysis/\", \"See corresponding config file\")'
    ndays = f'Number of days where DO < {thresh_filename} mg/L anywhere in Region (or in benthic layer of region if benthic case)' #Uses thresh_filename
    vd = f'Total volume of cells in region that experienced DO < {thresh_filename} mg/L over the course of the year' #uses thresh_filename
    pvd = f'Percent of regional volume that experienced DO < {thresh_filename} mg/L over the course of the year' #uses thresh_filename
    
    created_by = 'Stefano Mazzilli, adapted from original code from Rachael D. Mueller (see git repository)'
    created_at = 'Puget Sound Institute'
    created_from = 'Model results produced by Su Kyong Yun (PNNL) and Rachael Mueller (PSI)'
    created_on = date.today().strftime("%B %d, %Y")
    
    # Build README content with new format
    readme_content = [
        'Updated README for Excel',
        f'Created by: {created_by}',
        f'Created at: {created_at}',
        f'Created on: February 11, 2025',
        f'Created with model results produced by: {created_from}',
        '',  # Empty string instead of space to avoid zeros in Excel
        '=== SETTINGS ===',
        f'Threshold: {thresh_filename} mg/L (runs range 0-1000, where 1000 captures all)',
        f'Habitat: <80m depth, bottom layer only (crab)',
        '',  # Empty string instead of space to avoid zeros in Excel
        '=== TAB DESCRIPTIONS ===',
        f'Number_of_Days: Days where parameter < threshold anywhere in region',
        f'Volume_Days [km³×days]: Cumulative volume×days below threshold',
        f'Percent_Volume_Days[%]: Volume_Days / (Regional_Volume × 361 days) × 100',
        '',  # Empty string instead of space to avoid zeros in Excel
        f'Volume_Existing/Reference: Daily statistics for volume below threshold (with habitat mask by region)',
        f'Area_Existing/Reference: Daily statistics for area below threshold (with habitat mask by region)',
        f'Nodes_Existing/Reference: Daily statistics for nodes below threshold (with habitat mask by region)',
        '',  # Empty string instead of space to avoid zeros in Excel
        '=== KEY COLUMNS ===',
        'Total_[metric]: Full regional extent (Column B)',
        'Total_Habitat_[metric]: Habitat extent only (Column C)',
        'Avg/Min/Max/Unique_[metric]: All from habitat-filtered data',
        '',  # Empty string instead of space to avoid zeros in Excel
        'Current %ofTotal columns use Column B as denominator',
        '',  # Empty string instead of space to avoid zeros in Excel
        '=== MANUAL RECALCULATIONS ===',
        '',  # Empty string instead of space to avoid zeros in Excel
        'For ANY percentage shown, to get %ofHabitat:',
        'Formula: [Numerator] / [Column C Habitat value] × 100',
        '',  # Empty string instead of space to avoid zeros in Excel
        'Example:',
        'UniqueVol_%ofHabitat = Total_Unique_Vol_km3 / Total_Habitat_Vol_km3 × 100',
        '                      = 1.092 / 22.819 × 100 = 4.78%',
        '',  # Empty string instead of space to avoid zeros in Excel
        'For Percent_Volume_Days recalculation:',
        '%ofHabitat = Volume_Days / (Total_Habitat_Vol_km3 × 361) × 100'
    ]

    header_threshold = {
        'README': readme_content  # Changed from ' ' to 'README' for clearer column header
    }

    header_threshold_df = pandas.DataFrame(header_threshold)
    
    print('*************************************************************')
    print('Writing threshold analysis spreadsheet to: ', excel_output_path)
    print('*************************************************************')
    
    # Create Excel output directory if it doesn't exist
    if not os.path.exists(excel_output_path):
        print(f'creating: {excel_output_path}')
        os.umask(0)  # clears permissions
        os.makedirs(excel_output_path, mode=0o777, exist_ok=True)
    
    # Create scenario suffix from actual data 
    scenario_suffix = "-".join(dir_list).replace('_', '-')
    
# Write Excel file with all tabs for threshold analysis
    with pandas.ExcelWriter(
        pathlib.Path(excel_output_path)/f'{case}_{scope}_{excel_file_param_name}-lt-{thresh_filename}_{scenario_suffix}.xlsx', mode='w') as writer:
        DaysDOXGBelowThresh_df.to_excel(writer, sheet_name='Number_of_Days')
        VolumeDays_df.to_excel(writer, sheet_name='Volume_Days')
        PercentVolumeDays_df.to_excel(writer, sheet_name='Percent_Volume_Days')
        header_threshold_df.to_excel(writer, sheet_name='README', index=False)  # Added index=False to remove row numbers
        
    print(f'Excel file created: {excel_output_path}/{case}_{scope}_{excel_file_param_name}-lt-{thresh_filename}_{scenario_suffix}.xlsx') #Uses excel_file_param_name
    print("="*80)   
    
    # END EXCEL EXPORT SECTION
    
    # FUNCTION ENDS HERE - RETURN DATAFRAMES (EXCEL NOW EXPORTED INSIDE FUNCTION)
    #return DaysThreshold_df, VolumeThreshold_df, PercentVolumeThreshold_df, DOXGBelowThresh, volume2D  #added DOXGBelowThresh (361×10×4144) daily boolean arrays and volume2D (4144×10) volume arrays for daily analysis

    return DaysDOXGBelowThresh_df, VolumeDays_df, PercentVolumeDays_df,  volume2D, DOXGBelowThresh #SM added DOXGBelowThresh to return the (361×10×4144) daily boolean arrays for post-processing to find min/max volume days per region


# ==============================================================================
# FUNCTION CALL - THRESHOLD ANALYSIS FOR WATER COLUMN (MULTIPLE THRESHOLDS)
# ==============================================================================
thresholds_to_run = thresholds_to_run # DO: thresholds_to_run = [2, 5, "DO_standard"], MI = 1 and 2
all_threshold_results = {} #initalize

for DO_threshold in thresholds_to_run:
    results_threshold = calc_DO_below_thresh(
        case=case,
        DO_thresh=DO_threshold,
        shp=ssm_config['paths']['shapefile'],
        scope=scope, #defined earlier
        ssm_config=ssm_config,
        ssm_input_datasets=ssm_input_datasets
    )
       #excel_output_path = excel_output_path # defined in initialization section and used globally in this call to function

    DaysDOXGBelowThresh_df, VolumeDays_df, PercentVolumeDays_df, volume2D, DOXGBelowThresh = results_threshold  # Unpack with original names: volume2D contains (4144×10) volume arrays, DOXGBelowThresh contains (361×10×4144) daily boolean arrays

    # Rename during dictionary assignment  
    all_threshold_results[f'threshold_{DO_threshold}'] = {
        'DaysDOXGBelowThresh_df': DaysDOXGBelowThresh_df,           # DataFrame with regional aggregation
        'VolumeDays_df': VolumeDays_df,                           # DataFrame with regional aggregation
        'PercentVolumeDays_df': PercentVolumeDays_df,             # DataFrame with regional aggregation
        'volume2D_data': volume2D,                                # Renamed: volume arrays (4144×10) for water column
        'ParmBelowThresh_daily_data': DOXGBelowThresh             # Renamed: daily boolean arrays (361×10×4144)
    }


# ============================================================================
# ## Function: Calc. thresholds by regional based on daily volumes
# ============================================================================

# ==============================================================================
# DAILY VOLUME ANALYSIS - SUBSET TO SHAPEFILE NODES AND CALCULATE BY REGION
# Adapted and pattern following original calc_DO_below_thresh exactly, unless noted
#
# DATA STRUCTURE MAP e.g.:
# INPUT:  all_threshold_results['threshold_2']['volume2D_data'] → (16013,10) volume array in km³
#         all_threshold_results['threshold_2']['ParmBelowThresh_daily_data']['wqm_baseline'] → (361,10,16013) boolean array of cells below DO threshold
# OUTPUT: daily_volume_results['threshold_2']['wqm_baseline']['Hood'] → (361,) array of daily volumes in km³ 
# TRANSFORMATION: Extract regional nodes → multiply boolean×volume → sum across depths/nodes → daily totals
# TEST LOAD INPUT:  test_volume = all_threshold_results['threshold_2']['volume2D_data']
#                   test_boolean = all_threshold_results['threshold_2']['ParmBelowThresh_daily_data']['wqm_baseline']
# TEST LOAD OUTPUT: test_hood_daily = daily_volume_results['threshold_2']['wqm_baseline']['Hood']
#nested dic. for:                     daily_volume_results: threshold ->  scenario -> region 
#
# ==============================================================================

################### INITIALIZE AND SETUP: Load shapefile and define regions and region total volumes, and define time coordinates ###################
import pandas as pd  #import pandas for DataFrame operations
import numpy as np  #import numpy for array operations

# load shapefile for regional filtering (if not already loaded)
gdf = gpd.read_file(ssm_config['paths']['shapefile'])  #load shapefile with node locations and regional boundaries
gdf = gdf.rename(columns={'region_inf': 'Regions'})  # Rename region column name 
regions = gdf[['node_id', 'Regions']].groupby('Regions').count().index.to_list()  #get list of unique region names from shapefile
regions.remove('Other')  #exclude Other or any region from analysis 
regions.append('All_regions')  #add All_regions as virtual region representing all included nodes for combined analysis
#set time coordinates for 361 days starting 1/5/2014
dataset_start_date = pd.to_datetime('2014-01-05')  #define model start date matching SSM runs
time_coords = pd.date_range(dataset_start_date, periods=361, freq='D')  #create pandas date_range array of daily time index for full year

daily_volume_results = {}  #initalize for nested dictionary: threshold -> scenario -> region -> daily_volumes_array
# ==============================================================================
# Regional volumes already calculated earlier (after habitat masking section)
# ==============================================================================
# regional_volumes dictionary now contains effective habitat volumes calculated in prior cell (not static WC volumes)
# All downstream code (statistics DataFrames, Excel outputs, plot annotations) uses regional_volumes automatically
print(f"[DEBUG] Regional volumes defined for: {list(regional_volumes.keys())}")  #show which regions have volume data
print("[DEBUG] Starting daily volume analysis for all thresholds...")  
print(f"[DEBUG] Will analyze {len(all_threshold_results)} thresholds across {len(regions)} regions")  

####################### PROCESS EACH THRESHOLD #######################
##### Process each threshold - NESTED POSITION: creating daily_volume_results[threshold_key e.g. 'threshold_2'] top level
for threshold_key in all_threshold_results.keys():  #loop through 'threshold_2', 'threshold_5', etc.
    print(f"[DEBUG] Processing {threshold_key}...")  #show current threshold being processed
    
    #Get data for this threshold using same variable names as template
    volume2D = all_threshold_results[threshold_key]['volume2D_data']  #volume array (16013×10) full model grid km³ per cell
    DOXGBelowThresh = all_threshold_results[threshold_key]['ParmBelowThresh_daily_data']  #dict with (361×10×16013) boolean arrays per scenario
    print(f"[DEBUG] {threshold_key}: Working with volume array {volume2D.shape}")  #confirm array dimensions
    
    ##### 
    # Process each scenario - NESTED POSITION:: daily_volume_results[e.g. 'threshold_2'] exists, creating ['threshold_2'][run_type e.g. 'wqm_baseline'] level
    #Store daily results for this threshold in nested structure
    daily_volume_results[threshold_key] = {}  #initialize scenario-level dictionary for this threshold
    for run_type in DOXGBelowThresh.keys():  #iterate through scenario names (wqm_baseline, wqm_reference)
        print(f"[DEBUG] {threshold_key} - {run_type}: Starting daily volume calculation")  #show current scenario
        
        #Extract boolean array already prepared < threshold, for this scenario eg 'wqm_baseline'
        DOXGBelowThresh_scenario = DOXGBelowThresh[run_type]  #extract (361×10×16013) boolean array for current scenario
        #print(f"[DEBUG] {threshold_key} - {run_type}: Boolean array shape {DOXGBelowThresh_scenario.shape}")  
                
        ##### 
        # Calculate daily volumes by region - NESTED POSITION: daily_volume_results[e.g. 'threshold_2'][e.g. 'wqm_baseline'][region e.g. 'Hood'] ← creating final level
        daily_volume_results[threshold_key][run_type] = {}  #initialize region-level dictionary for this scenario
        
        #Loop through regions
        for region in regions:  #iterate through each region (Hood, Main, SJF_Admiralty, etc.)
        #Create conditional boolean mask for All_regions vs individual regions
            if region == 'All_regions':
                idx_pandas = (gdf['included_i'] == 1)  #boolean mask selecting all 4144 included nodes across all regions
            else:
                idx_pandas = ((gdf['Regions'] == region) & (gdf['included_i'] == 1))  #boolean mask selecting nodes in current region that are included in analysis
            idx = np.asarray(idx_pandas, dtype=bool)  #convert pandas Series to numpy bool array to avoid mixed-type operations

            print(f"[DEBUG] {threshold_key} - {run_type} - {region}: Found {idx.sum()} nodes in region") #show number of nodes found (Hood=401, Main=893, etc.) by counting True values in boolean mask array
            #### Calculate volume for each day instead total across all days as in prior regional excels of noncompliance and < threshold DO
            #Extract regional volume data and booleen thesholds using  indexing pattern
            RegionVolume_2D = volume2D[idx, :]  #extract volume for region nodes from full grid: (N_region_nodes×10)
            RegionBoolean_3D = DOXGBelowThresh_scenario[:, :, idx]  #extract boolean for region nodes from full grid: (361×10×N_region_nodes)
            #Calculate daily volume using vectorized operations , but not summed- preserve daily dimension
            #RegionVolume_2D is (N_region×10), RegionBoolean_3D is (361×10×N_region) 
            RegionVolume_expanded = RegionVolume_2D[np.newaxis, :, :] #expand volume from 2D (N_region×10) to 3D (1×N_region×10) with singleton dimension for broadcasting
            RegionBoolean_transposed = RegionBoolean_3D.transpose(0, 2, 1) #transpose from (361×10×N_region) days×depths×nodes to (361×N_region×10) days×nodes×depths to match RegionVolume_expanded axis order for element-wise multiplication
            DailyVolume_3D = RegionVolume_expanded * RegionBoolean_transposed  #element-wise multiply volume×boolean: (361×N_region×10)
            DailyVolume_1D = DailyVolume_3D.sum(axis=(1, 2)) #sum over axis 1 (nodes) and axis 2 (depths), keeping axis 0 (days) to get (361,) daily total volumes in km³ - equivalent to prior threshold regional total but preserving daily dimension
            
            #store daily volume array instead of single total like template
            daily_volume_results[threshold_key][run_type][region] = DailyVolume_1D  #store 361-day volume array for this combination
            
            #Min/max volume days for analysis (template only calculated totals)
            min_day_idx = np.argmin(DailyVolume_1D)  #find day index with minimum volume below threshold
            max_day_idx = np.argmax(DailyVolume_1D)  #find day index with maximum volume below threshold
            print(f"[DEBUG] {threshold_key} - {run_type} - {region}: Min volume day {min_day_idx} ({time_coords[min_day_idx].date()}), Max volume day {max_day_idx} ({time_coords[max_day_idx].date()})")  #show min/max days found

        # BR: added for QA
        pd.DataFrame(daily_volume_results[threshold_key][run_type]).to_excel(excel_output_path + f'/{case}_{scope}_{excel_file_param_name}-dailyVols-{threshold_key}_{run_type}.xlsx')

print(f"[DEBUG] Daily volume analysis complete. Results stored in daily_volume_results dictionary.")  #final status message

