#!/usr/bin/env python
"""
[REMOVABLE - ALL COMMENTED CODE]
Non-compliance Analysis Functions (COMMENTED ONLY)
Cells 23,24,26,28-34 from original notebook
All code in this file is commented out in the original notebook
Active code from cells 25,27 has been moved to 2d_prepare_threshold_input_data.py
"""


# ============================================================================
# # ### Analysis Code And Plot/Excel outputs:###
# ============================================================================

# ##DEBUG: # Example V2 Metabolic Data Access:**
# # Access minimum metabolic index for salmon water column
# data = SSMcalcs_dic[f'CalMinParam_2D_{taxa}_Mindex_routine']['exist'][f'Mindex_{taxa}_routine_wc']
# # Access with confidence intervals
# data_upper = SSMcalcs_dic[f'CalMinParam_2D_{taxa}_Mindex_routine_ci_upper']['exist'][f'Mindex_{taxa}_routine_ci_upper_wc']
# data_lower = SSMcalcs_dic[f'CalMinParam_2D_{taxa}_Mindex_routine_ci_lower']['exist'][f'Mindex_{taxa}_routine_ci_lower_wc']

# SSMcalcs_dic.keys()  #show available datasets loaded

# existing_data= SSMcalcs_dic['CalMinParam_3D_crab_Mindex_routine']['exist']
# reference_data= SSMcalcs_dic['CalMinParam_3D_crab_Mindex_routine']['wqm_reference']
# existing_data.keys


# ============================================================================
# # Non compliant function and excel export
# ============================================================================


# ===== Cell 25 content moved to 2d_prepare_threshold_input_data.py ===== #CHANGED


# ============================================================================
# ### Mapping loaded data to the non compliant functions following
# ============================================================================


# ===== Cell 27 content moved to 2d_prepare_threshold_input_data.py ===== #CHANGED

#xyx prob


# ============================================================================
# ## Function:calc_noncompliant
# ============================================================================

# # ==============================================================================
# # EMBEDDED CALC_NONCOMPLIANT FUNCTION 
# #SM- Modified to use simple data mapping approach above instead of YAML+inspect approach
# # ==============================================================================

# # All required imports for the embedded function done earlier

# def calc_noncompliant(shp, case, scope, ssm_config, ssm_input_datasets, human_allowance=-0.2, non_compliant_threshold=-0.25):  #Accept ssm_input_datasets as parameter instead of using globals
#     """
#     calc_noncompliant function - data passed as parameter
#     """
#     # ********************************************************************
#     # SECTION 1: INITIALIZATION
#     # ********************************************************************
    
#     # Use passed dataset directly
#     MinDO_full = ssm_input_datasets  # passed dataset directly, keep internal variable name for minimal code changes -NOTE this may be max or mean andmay be other than DO passed in
    
#     # Initialize dictionaries
#     MinDO={} # Min, daily DO over all nodes in shapefile
#     DO_diff_lt_0p2={} # Boolean where DO<threshold
#     DO_diff_lt_0p2_days={} # Number of days where DOBelowThresh = True
#     DaysNonCompliant={} # Sum of days across regions
#     VolumeDaysNonCompliant={} # Percent of volume within region where DO<threshold
#     PercentVolumeDaysNonCompliant={}
#     AreaNonCompliant={}
     
#     # Define dimension sizes and load shapefile
#     gdf = gpd.read_file(shp)
#     gdf = gdf.rename(columns={'region_inf':'Regions'})
#     regions = gdf[['node_id','Regions']].groupby(
#         'Regions').count().index.to_list()
#     regions.remove('Other')   # note:comment this line if you need to keep other
    
#     # ********************************************************************
#     # SECTION 2: DATA LOADING (SIMPLE MAPPING APPROACH)
#     # ********************************************************************
#     #Use pre-loaded data from global MinDO_full dictionary instead of YAML+inspect approach
#     print("Using pre-loaded data from mapping cell") #global MinDO_full defined earlier

#     # Check if data is available - ensures mapping cell was executed before function call
#     if not MinDO_full:  # Validate that data mapping cell populated the global dictionary before proceeding
#         raise ValueError("MinDO_full dictionary is empty. Run the data mapping cell first.")
    
#     print(f"Found data for scenarios: {list(MinDO_full.keys())}")  # Display available scenario names for debugging
    
#     # Subset to shapefile nodes for each scenario - extract only nodes present in shapefile from full model grid
#     for run_dir in MinDO_full.keys():  # Iterate through all scenario names (keys) in the pre-loaded data dictionary
#         if scope == 'benthic':
#             MinDO[run_dir] = MinDO_full[run_dir][:, gdf['node_id'].values-1]  #SM- added .values to convert pandas Series to numpy array for proper indexing - MinDO_full contains all 16012 nodes, subset to shapefile nodes only
#         else:  # water column
#             MinDO[run_dir] = MinDO_full[run_dir][:, :, gdf['node_id'].values-1]  #SM- added .values to convert pandas Series to numpy array for proper indexing - 3D array (time, depth, nodes) subset to shapefile nodes
    
#     # Set dimensions from loaded data
#     first_key = list(MinDO.keys())[0]
#     if scope == 'benthic':
#         ndays, nnodes = MinDO[first_key].shape
#         DO_std = np.tile(gdf.DO_std, (ndays, 1))
#         unmasked = np.tile(gdf.included_i, (ndays, 1))
#     else:  # water column
#         ndays, nlevels, nnodes = MinDO[first_key].shape
#         DO_std = np.tile(gdf.DO_std, (ndays, nlevels, 1))
#         unmasked = np.tile(gdf.included_i, (ndays, nlevels, 1))
    
#     # Create dir_list from loaded data keys
#     dir_list = list(MinDO.keys())
    
#     # ********************************************************************
#     # SECTION 3: VOLUME CALCULATIONS
#     # ********************************************************************
    
#     # Calculate volume for volume days
#     if scope=='benthic':
#         volume = np.asarray(
#             gdf.volume*ssm_config['siglev_diff'][-1]/100) # just the bottom level
#     else: # water column
#         volume = np.asarray(gdf.volume)
#         depth_fraction = np.array(ssm_config['siglev_diff'])/100
#         volume2D = np.dot(volume.reshape(nnodes,1),depth_fraction.reshape(1,nlevels))
#     # Define reference run
#     reference = ssm_config['run_information']['reference']
#     dir_list.remove(reference)
    
#     # ********************************************************************
#     # SECTION 4: NON-COMPLIANCE CALCULATIONS
#     # ********************************************************************
    
#     # Loop through all non-reference runs and calculate non_compliant_threshold
#     for run_type in dir_list:
#         print(f'Calculating difference for {run_type}')
#         # Create array of Dissolved Oxygen threshold values 
#         DO_diff = MinDO[run_type] - MinDO[reference]
#         # Boolean where DO_diff < -0.2 (or non_compliant_threshold value)
#         # Part-B Noncompliance:
#         # - Min DO for reference case < DO standard + human limit (0.2 mg/l) and 
#         # - DO difference between case and reference is less than threshold (-0.2 or -0.25 for "rounding method")
#         DO_diff_lt_0p2_result = (
#             (DO_diff<=non_compliant_threshold) &   #361x4144 (nodes x time) or 361x10x4144
#             (MinDO[reference] < DO_std + human_allowance) &
#             (unmasked==1)
#         )
#         # Ensure result is pure numpy array (not pandas/xarray object)
#         DO_diff_lt_0p2[run_type] = np.asarray(DO_diff_lt_0p2_result, dtype=bool)  #Convert mixed pandas/xarray to numpy bool array - pandas Series & xarray objects cause errors in numpy operations like .max(where=) and .sum(), dtype=bool ensures True/False not 1/0 floats
#         # Number of days where DO < threshold = True
#         if scope=='benthic':
#             DO_diff_lt_0p2_days[run_type]=DO_diff_lt_0p2[run_type].sum(
#                 axis=0, initial=0) #4144 (nodes) or 10x4144
#             VolumeDays_all=volume*DO_diff_lt_0p2_days[run_type]
#         else: # water column: sum over days and take max value over depth
#             # First get a count of days noncompliant for each depth level
#             DO_diff_lt_0p2_days_wc=DO_diff_lt_0p2[run_type].sum(
#                 axis=0, initial=0)
#             # Volume days: Use days noncompliant for each level  and element-wise 
#             # multiplication of 10x4144 * 10x4144 matrices to get volume days by level
#             VolumeDays_wc=volume2D.transpose()*DO_diff_lt_0p2_days_wc
#             # Add across levels to get total VolumeDays per node
#             VolumeDays_all = VolumeDays_wc.sum(axis=0)
        
#         # Total number of days and percent volume days for each region
#         DaysNonCompliant[run_type]={}
#         AreaNonCompliant[run_type]={}
#         VolumeDaysNonCompliant[run_type]={}
#         PercentVolumeDaysNonCompliant[run_type]={}
#         for region in regions:
#             # create boolean of indices where True selects nodes of 
#             # specified Region 
#             idx_pandas = ((gdf['Regions']==region) &
#                    (gdf['included_i']==1))
#             idx = np.asarray(idx_pandas, dtype=bool)  #SM- Convert mixed pandas/xarray to numpy bool array - pandas Series & xarray objects cause errors in numpy operations like .max(where=) and .sum(), dtype=bool ensures True/False not 1/0 floats
#             # Note: The max of True/False will be True and initial sets False to zero.
#             # The "where" keywork specifies to only use values where idx=True,
#             # which in this case I set to specify the region.
#             if scope=='benthic':
#                 # Assign the maximum (True) of DO < threshold occurrence anywhere in region
#                 # then sum values over time
#                 DaysNonCompliant[run_type][region] = DO_diff_lt_0p2[run_type].max(
#                     axis=1,where=idx,initial=0).sum().item()
#             else:
#                 # Assign the maximum (True) of DO < threshold occurrence across depths 
#                 # such that 1-day of non-compliance is counted if there is one or more 
#                 # levels noncompliant
#                 DOBelowThresh_daysnodes = DO_diff_lt_0p2[run_type].max(axis=1,initial=0)
#                 # Assign the maximum (True) of DO < threshold occurrence 
#                 # anywhere in region then sum values over time
#                 DaysNonCompliant[run_type][region] = DOBelowThresh_daysnodes.max(
#                     axis=1,where=idx,initial=0).sum().item()                
            
#             # Estimate Volume Days non-compliant
#             VolumeDaysNonCompliant[run_type][region]=np.array(VolumeDays_all)[
#                 (gdf['Regions']==region) &
#                 (gdf['included_i']==1)
#             ].sum()
#             # Calculate area of non-compliance in regions
#             # I'm not sure why this next step is needed but it is.  
#             # Querying the dataframe with (VolumeDays_all>0) raises a reshape error (???)
#             gdf['VolumeDays_all']=VolumeDays_all  
#             AreaNonCompliant[run_type][region] = 1e-6 * gdf.Area_m2.loc[
#                     (gdf['Regions']==region) &
#                     (gdf['included_i']==1) &
#                     (gdf['VolumeDays_all']>0)
#             ].sum().item()
#                          # Sum all areas and convert m² to km² (multiply by 1e-6)

#             # get regional volume
#             if scope=='benthic': # take fraction for bottom-level volume
#                 RegionVolume = ssm_config['siglev_diff'][-1]/100*volume[
#                     (gdf['Regions']==region) &
#                     (gdf['included_i']==1)
#                 ].sum()
#             else: # water column
#                 RegionVolume = volume[
#                     (gdf['Regions']==region) &
#                     (gdf['included_i']==1)
#                 ].sum()
#             PercentVolumeDaysNonCompliant[run_type][region]=100*(
#                 VolumeDaysNonCompliant[run_type][region]/(RegionVolume*ndays)
#             )
#         #end of region loop
#         # Then calculate ALL_REGIONS area total for area non-compliance as not a predefined region
#         # This sums the area of ALL nodes (not just specifc regions) where any non-compliance occurred
#         AreaNonCompliant[run_type]['ALL_REGIONS'] = 1e-6 * gdf.Area_m2.loc[
#             (gdf['included_i']==1) &              # Only include nodes marked as included (excludes boundary nodes)
#             (gdf['VolumeDays_all']>0)             # Only nodes where volume*days > 0 (had non-compliance)
#         ].sum().item()   
        
#         #all regions in dataframe calculations:
#         #Days: 
#         # Create totals across entire domain.  This includes "Other" nodes. 
#         # I tested np.asarray(VolumeDays_all)[idx], where 
#         # idx = (gdf['Regions']!='Other')
#         # and VolumeDays_all.sum().item().  They give the same number, 
#         # so I'm keeping the 29 "Other" nodes in for now
#         #Days: SM - Add inclusion filter because ALL_REGIONS was counting excluded nodes that individual regions ignore
#         if scope=='benthic': #(361x4771): max over nodes and sum over time
#             #ALL_REGIONS needs to be calculated separately as it's not in the "regions" list, calculation finds all days where any included node was non-compliant
#             idx_all_included = (gdf['included_i'] == 1).values #create boolean mask selecting only nodes that are included in analysis to match regional filtering logic
#             DaysNonCompliant[run_type]['ALL_REGIONS'] = DO_diff_lt_0p2[run_type].max(
#                 axis=1, where=idx_all_included, initial=0).sum(axis=0,initial=0).item() #axis=1 takes maximum boolean value across all included nodes for each day to find if any included node was non-compliant, where= applies inclusion filter to only consider included nodes, initial=0 returns False when no included nodes found, sum() counts number of days with True values meaning days with non-compliance
#         else: #(361x10x4771): max over nodes and depth and sum over time
#             DOBelowThresh_daysnodes = DO_diff_lt_0p2[run_type].max(axis=1,initial=0) #axis=1 takes maximum boolean value over all depth levels for each day/node combination to find if any depth at that node was non-compliant, initial=0 returns False when no depths found
#             #ALL_REGIONS needs to be calculated separately as it's not in the "regions" list, calculation finds all days where any included node at any depth was non-compliant
#             idx_all_included = (gdf['included_i'] == 1).values #create boolean mask selecting only nodes that are included in analysis to match regional filtering logic  
#             DaysNonCompliant[run_type]['ALL_REGIONS'] = DOBelowThresh_daysnodes.max(
#                 axis=1, where=idx_all_included, initial=0).sum().item() #axis=1 takes maximum boolean value across all included nodes for each day to find if any included node was non-compliant, where= applies inclusion filter to only consider included nodes, initial=0 returns False when no included nodes found, sum() counts number of days with True values meaning days with non-compliance
        
#         #volume and % volume
#         VolumeDaysNonCompliant[run_type]['ALL_REGIONS'] = VolumeDays_all.sum().item()
#         PercentVolumeDaysNonCompliant[run_type]['ALL_REGIONS'] = 100*(
#             VolumeDays_all.sum().item()/(volume.sum().item()*ndays)
#         )
    
#     # ********************************************************************
#     # SECTION 5: DATAFRAME CREATION AND RETURN
#     # ********************************************************************
    
#     print(case)
#     print([*ssm_config['run_information']['run_description_short']])
#     # Create a list of column header names using the keys in "run_description_short" to map to the desired name
#     # run_description_short can be used to change the run_tag if a different tag is wanted than what is used on Hyak to 
#     # organize runs
#     tag_list = [ssm_config['run_information']['run_tag'][case][tag] for tag in [*ssm_config['run_information']['run_description_short'][case]]]
#     tag_list.remove('Reference')
#     print("tag_list",tag_list)
   
#     # Convert to dataframe and organize information
#     DaysNonCompliant_df = pandas.DataFrame(DaysNonCompliant)
#     # rename column names using dictionary (repeat this method below)
#     DaysNonCompliant_df = DaysNonCompliant_df.rename(
#         columns=ssm_config['run_information']['run_tag'][case])
#     # sort order of columns based on order of dictionary; otherwise, python will choose order (repeat this method below)
#     DaysNonCompliant_df = DaysNonCompliant_df.reindex(columns=tag_list)
#     # Area non-compliant
#     AreaNonCompliant_df = pandas.DataFrame(AreaNonCompliant)
#     AreaNonCompliant_df = AreaNonCompliant_df.rename(
#         columns=ssm_config['run_information']['run_tag'][case])
#     AreaNonCompliant_df = AreaNonCompliant_df.reindex(columns=tag_list)
#     # Percent of volume over the year in each region where DO change < threshold
#     VolumeDaysNonCompliant_df = pandas.DataFrame(VolumeDaysNonCompliant)
#     VolumeDaysNonCompliant_df = VolumeDaysNonCompliant_df.rename(
#         columns=ssm_config['run_information']['run_tag'][case])
#     # rename columns to more readable (neccessary for SOG_NB, not so much for whidbey)
#     VolumeDaysNonCompliant_df = VolumeDaysNonCompliant_df.reindex(columns=tag_list)
#     # Percent of cumulative volume over the year in each region where DO change < threshold
#     PercentVolumeDaysNonCompliant_df = pandas.DataFrame(PercentVolumeDaysNonCompliant)
#     PercentVolumeDaysNonCompliant_df = PercentVolumeDaysNonCompliant_df.rename(
#         columns=ssm_config['run_information']['run_tag'][case])
#     PercentVolumeDaysNonCompliant_df = PercentVolumeDaysNonCompliant_df.reindex(
#         columns=tag_list
#     )
    
#     # FUNCTION ENDS HERE - RETURN DATAFRAMES ONLY (NO EXCEL EXPORT IN FUNCTION as done after call )
#     return DaysNonCompliant_df, AreaNonCompliant_df, VolumeDaysNonCompliant_df, PercentVolumeDaysNonCompliant_df, volume2D, DO_diff_lt_0p2  #SM added volume2D (4144×10) volume arrays and DO_diff_lt_0p2 (361×10×4144) daily boolean arrays for non-compliance daily analysis


# ============================================================================
# ## Call non_compliant function
# ============================================================================

# print("=== RUNNING 3D WATER COLUMN NON-COMPLIANCE ANALYSIS ===")
# results_wc = calc_noncompliant(
#     shp=ssm_config['paths']['shapefile'],
#     case=case,
#     scope='wc',
#     ssm_config=ssm_config,
#     ssm_input_datasets=ssm_input_datasets,  #Pass already prepared data as parameter 
#     human_allowance=-0.2,
#     non_compliant_threshold=-0.25
# )
# # UNPACK RESULTS: 
# #old:
# #DaysNonCompliant_df, AreaNonCompliant_df, VolumeDays_df, PercentVolumeDays_df = results_wc
# # NEW (will work):
# DaysNonCompliant_df, AreaNonCompliant_df, VolumeDays_df, PercentVolumeDays_df, volume2D, DO_diff_lt_0p2 = results_wc  #renamed to match Excel export expectations: VolumeDaysNonCompliant_df becomes VolumeDays_df, PercentVolumeDaysNonCompliant_df becomes PercentVolumeDays_df for Excel compatibility

# # Storage for later use:
# noncompliant_results = {
#     'DaysNonCompliant_df': DaysNonCompliant_df,
#     'AreaNonCompliant_df': AreaNonCompliant_df,
#     'VolumeDays_df': VolumeDays_df,                    #using Excel-compatible names
#     'PercentVolumeDays_df': PercentVolumeDays_df,      #sing Excel-compatible names  
#     'volume2D_data': volume2D,
#     'DO_diff_lt_0p2_daily_data': DO_diff_lt_0p2
# } 


# ============================================================================
# ## Export Results to Excel File with Multiple Tabs (non compliant only)
# ============================================================================

# # ==============================================================================
# # EXCEL EXPORT - NOW SEPARATE FROM FUNCTION (MATCHES ORIGINAL STRUCTURE)
# # ==============================================================================

# # Convert non_compliant_threshold to text string for file name
# noncompliant_txt = str(-0.25).replace('.','p').replace('-','m')  # -0.25 → m0p25
# human_allowance = -0.2  # Keep track of parameters used

# # Create Excel output path
# excel_output_path = excel_output_path # defined in initialization section
# # Create README information
# this_file = '=HYPERLINK("https://github.com/UW-PSI/SalishSeaModel-analysis/")'
# run_description = '=HYPERLINK("https://github.com/UW-PSI/SalishSeaModel-analysis/", "See corresponding config file")'
# non_compliant_threshold_text = f'-0.25 mg/l'
# noncompliant = f'Non Compliant in this table is defined as < -0.25 mg/l. A non_compliant_threshold threshold of -0.25 is described in pages 49 and 50 of the Optimization report appendix.'
# noncompliant_link = '=HYPERLINK("https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf", "Optimization Report Appendix")'
# HA = f"{human_allowance}: Pre-industrial DO must be less than DO standard plus human allowance to be considered for Part B of the Dept. of Ecology's non-compliance calculation"
# ndays = f'Number of days where DO(scenario) - DO(reference) < -0.25 anywhere in Region (or in benthic layer of region if benthic case)'
# vd = f'Total volume of cells in region (or benthic layer in region) that experienced DO(scenario) - DO(reference) < -0.25 over the course of the years'
# pvd = f'Percent of regional (or benthic) volume that experienced DO(scenario) - DO(reference) < -0.25 over the course of the year'

# created_by = 'Stefano Mazzilli, adapted from original code from Rachael D. Mueller (see git repository)'
# created_at = 'Puget Sound Institute'  
# created_from = 'SSM runs for PSI activities originally produced by Su Kyong Yun (PNNL) and Rachael Mueller (PSI)'
# created_on = date.today().strftime("%B %d, %Y")

# header = {
#     ' ':[created_by, created_at, created_on, this_file, 
#         created_from, 
#         run_description, non_compliant_threshold_text, noncompliant, 
#         noncompliant_link, ndays, HA, vd, pvd]
# }

# header_df = pandas.DataFrame(header, index=[
#     'Created by',
#     'Created at',                           
#     'Created on',
#     'Created with',
#     'Contacts',
#     'Modeling by',
#     'Model Run Overview',
#     'Non Compliant threshold [mg/l]',
#     'Non Compliant Reference',
#     'NonCompliant_Days',
#     'Human Allowance [mg/l]',
#     'Volume_Days [km^3 days]',
#     'Percent_Volume_Days[%]'])

# # Create Excel output directory if it doesn't exist
# print('*************************************************************')
# print('Writing spreadsheet to: ', excel_output_path)
# print('*************************************************************')

# if not os.path.exists(excel_output_path):
#     print(f'creating: {excel_output_path}')
#     os.umask(0) #clears permissions
#     os.makedirs(excel_output_path, mode=0o777, exist_ok=True)

# # Write Excel file with all tabs
# with pandas.ExcelWriter(
#     pathlib.Path(excel_output_path)/f'{case}_wc_noncompliant_{noncompliant_txt}.xlsx', mode='w') as writer:
#     DaysNonCompliant_df.to_excel(writer, sheet_name='NonCompliant_Days')
#     AreaNonCompliant_df.to_excel(writer, sheet_name='Area_NonCompliant')
#     VolumeDays_df.to_excel(writer, sheet_name='Volume_Days')
#     PercentVolumeDays_df.to_excel(writer, sheet_name='Percent_Volume_Days')
#     header_df.to_excel(writer, sheet_name='README')
    
# print(f'Excel file created: {excel_output_path}/{case}_wc_noncompliant_{noncompliant_txt}.xlsx')
# print("="*80)

