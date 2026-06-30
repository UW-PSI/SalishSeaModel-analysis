#!/usr/bin/env python
"""
Create Volume Statistics DataFrames
Cells 43-45 from original notebook
Includes min/avg/max statistics and Excel export
"""


# ============================================================================
# ## Min Avg statistics for threshold volumes -Adds tab volume_exist/reference to existing excel
# ============================================================================

def print_volume_statistics(threshold_key, regions_to_plot, regional_total_volumes=None):
    """
    Print comprehensive statistics and create DataFrames for Excel export
    """
    
    # Using scenario_labels initialized at beginning of script workflow

    print(f"=== COMPREHENSIVE STATISTICS FOR {threshold_key.upper()} ===\n")

    # Get DataFrames
    dfs = create_statistics_dataframes(case, ssm_config, 'volume', daily_volume_results[threshold_key], regions_to_plot, time_coords)
    df_existing = dfs['wqm_baseline']
    df_reference = dfs['wqm_reference']

    # Print both tables
    for scenario, df, label in [('wqm_baseline', df_existing, scenario_labels['wqm_baseline']), ('wqm_reference', df_reference, scenario_labels['wqm_reference'])]:
        print(f"--- {label} ---")
        print(df.to_string(index=False, max_colwidth=12, col_space=10))
        print() # extra line after each table
    
    # Store DataFrames globally for Excel export later
    globals()[f'df_{threshold_key}_existing'] = df_existing
    globals()[f'df_{threshold_key}_reference'] = df_reference
    
    return df_existing, df_reference

# ==============================================================================
# REGIONAL VOLUME DATA - PROVIDED BY USER
# ==============================================================================


# regional_volumes =regional_volumes #from earlier daily volume section  # Total volume for each region in km³

# Loop through all thresholds for statistics
#regions = regions  #use regions list dynamic from earlier daily volume section (line with gdf shapefile extraction), includes toggle for Other 
regions = ['All_regions', 'Hood', 'Main', 'SJF_Admiralty', 'SOG_Bellingham', 'South_Sound', 'Whidbey']  #match fixed_regions order for stats  # NOTE: To manually override for custom selection eg all first and no "other", comment out above and use:
for threshold_key in daily_volume_results.keys():  #loop through all available thresholds
    print_volume_statistics(threshold_key, regions, regional_volumes)  # uses regions instead of all_region

# ==============================================================================
# ADD DETAILED VOLUME TABS TO EXISTING THRESHOLD EXCELS (WITH TAB ORDER CONTROL)
# ==============================================================================

def add_volume_tabs_to_existing_excels():
    """
    Add detailed volume statistics tabs to existing threshold Excel files
    Inserts Volume_Existing/Volume_Reference tabs after Number_of_Days tab
    """
    
    #excel_output_path = excel_output_path # defined in initialization section
    
    # Process each loaded threshold
    for threshold_key in daily_volume_results.keys():
        if threshold_key.startswith('threshold_') and threshold_key != 'threshold_DO_standard':
            # Extract threshold number for filename matching
            thresh_num = threshold_key.replace('threshold_', '')
            filename_pattern = f'{case}_{scope}_{excel_file_param_name}-lt-{thresh_num}_*.xlsx'  # uses same file name variable defined earlier for DO/MI compatibility
        elif threshold_key == 'threshold_DO_standard':
            # Special case for DO_standard
            filename_pattern = f'{case}_{scope}_{excel_file_param_name}-lt-DO_standard_*.xlsx' # uses same file name variable defined earlier for DO/MI compatibility
        else:
            continue  #skip non-threshold keys
        
        # Find matching Excel file
        excel_dir = pathlib.Path(excel_output_path)  # Convert string to Path locally
        matching_files = list(excel_dir.glob(filename_pattern))
        
        if not matching_files:
            print(f"[WARNING] No Excel file found for {threshold_key} with pattern {filename_pattern}")
            continue
        
        excel_file = matching_files[0]  #take first match
        
        # Read all existing sheets first to preserve order
        existing_data = {}
        with pd.ExcelFile(excel_file) as xls:
            for sheet_name in xls.sheet_names:
                existing_data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)

        # Habitat selection - Use volume2D_masked which already has habitat mask applied and uses full grid indexing
        habitat_volumes = {}
        for region in regions:
            region_mask_habitat = (gdf['Regions'] == region) & (gdf['included_i'] == 1) if region != 'All_regions' else (gdf['included_i'] == 1)  #get mask for nodes in this region (for habitat calculation)
            region_indices_habitat = np.where(region_mask_habitat)[0]  #array indices for this region's nodes (for habitat calculation)
            habitat_volumes[region] = np.nansum(volume2D_masked[region_indices_habitat, :])  #sum habitat-masked volume for region; volume2D_masked already has habitat mask applied

        # Get detailed volume statistics for this threshold
        dfs = create_statistics_dataframes(case, ssm_config, 'volume', daily_volume_results[threshold_key], regions, time_coords, habitat_sizes=habitat_volumes)
        df_existing = dfs['wqm_baseline']
        df_reference = dfs['wqm_reference']

        # Write all sheets in desired order: Number_of_Days, Volume_Existing, Volume_Reference, then rest
        with pd.ExcelWriter(excel_file, mode='w', engine='openpyxl') as writer:
            # First: Number_of_Days
            if 'Number_of_Days' in existing_data:
                existing_data['Number_of_Days'].to_excel(writer, sheet_name='Number_of_Days', index=False)
            
            # Second: Volume_Existing and Volume_Reference
            df_existing.to_excel(writer, sheet_name='Volume_Existing', index=False)
            df_reference.to_excel(writer, sheet_name='Volume_Reference', index=False)
            
            # Third: All remaining sheets in original order
            for sheet_name, data in existing_data.items():
                if sheet_name != 'Number_of_Days':  #skip since already written
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"Added Volume_Existing and Volume_Reference tabs after Number_of_Days in {excel_file.name}")

# Run the function to add volume tabs
add_volume_tabs_to_existing_excels()
#excel_output_path = excel_output_path # defined in initialization section and used in function

