#!/usr/bin/env python
"""
Create Area and Node Statistics DataFrames with Excel Export
Cells 58-61 from original notebook
"""


# ============================================================================
# ## Area statistics to excel tables (avg min and max)-adds tabs to existing excel:
# ============================================================================

# ==============================================================================
# AREA ANALYSIS - COMPLETE PROCESSING BLOCK
# ==============================================================================
# This block adds Area analysis parallel to Volume analysis
# Follows EXACT noncompliant area calculation pattern (sum Area_m2 where cells below threshold)
# Output Excel tabs: Area_Existing, Area_Reference (same structure as Volume tabs)
# ==============================================================================

# ==============================================================================
# Area Sec. 1: Calculate Regional Total Areas from Shapefile
# ==============================================================================
# Calculate total area for each region from gdf.Area_m2 column
# Follows noncompliant pattern: filter by region+included_i, sum Area_m2, convert m² to km²

print("Calculating regional total areas from shapefile...")
regional_areas = {}  #initialize dictionary to store total area (km²) for each region
for region in regions:  #iterate through all regions including All_regions
    if region == 'All_regions':
        idx = (gdf['included_i'] == 1)  #All_regions uses all included nodes across entire domain
        regional_areas[region] = (gdf.Area_m2[idx].sum()) * 1e-6  #sum all included node areas, convert m² to km²
    else:
        idx = (gdf['Regions'] == region) & (gdf['included_i'] == 1)  #individual region filters by region name and included status
        regional_areas[region] = (gdf.Area_m2[idx].sum()) * 1e-6  #sum regional node areas, convert m² to km²

print(f"Regional areas calculated: {list(regional_areas.keys())}")  #show which regions have area data
print("Sample areas (km²):", {k: f"{v:.2f}" for k, v in list(regional_areas.items())[:3]})  #display first 3 regions as verification

# ==============================================================================
# Area Sec. 2: Daily Area Extraction Loop
# ==============================================================================
# Extract daily areas below threshold for each region/scenario
# For each day, identifies which cells have any depth below threshold, then sums their areas
# Creates daily_area_results dictionary with 361-day area arrays for each threshold/scenario/region

print("\n=== Starting Daily Area Extraction ===")
daily_area_results = {}  #initialize nested dictionary: daily_area_results[threshold][scenario][region] = 361-day array of daily areas in km²

for threshold_key in all_threshold_results.keys():  #iterate through all thresholds (threshold_1, threshold_2, threshold_5, threshold_DO_standard, etc.)
    print(f"Processing {threshold_key}...")
    
    volume2D = all_threshold_results[threshold_key]['volume2D_data']  #(N_nodes×10) volume array - not used for area but loaded for consistency with pattern
    DOXGBelowThresh = all_threshold_results[threshold_key]['ParmBelowThresh_daily_data']  #dict with (361×10×16013) boolean arrays where True = below threshold
    
    daily_area_results[threshold_key] = {}  #initialize scenario level for this threshold
    
    for run_type in DOXGBelowThresh.keys():  #iterate through scenarios: 'wqm_baseline', 'wqm_reference'
        print(f"  {threshold_key} - {run_type}: Starting daily area calculation")
        
        DOXGBelowThresh_scenario = DOXGBelowThresh[run_type]  #extract (361×10×16013) boolean array for current scenario
        daily_area_results[threshold_key][run_type] = {}  #initialize region level for this scenario
        
        for region in regions:  #iterate through each region including All_regions
            if region == 'All_regions':
                idx_pandas = (gdf['included_i'] == 1)  #All_regions uses all included nodes
            else:
                idx_pandas = ((gdf['Regions'] == region) & (gdf['included_i'] == 1))  #individual region filters by region name and included status
            idx = np.asarray(idx_pandas, dtype=bool)  #convert pandas Series to numpy boolean array for indexing
            
            region_node_indices = np.where(idx)[0]  #get array indices of nodes in this region
            region_areas_m2 = gdf.Area_m2.iloc[region_node_indices].values  #extract area of each node in this region (m²)
            
            daily_areas = np.zeros(361)  #initialize array to store area (km²) for each of 361 days
            
            for day_idx in range(361):  #loop through each day of the year
                day_boolean_full = DOXGBelowThresh_scenario[day_idx, :, :]  #extract boolean for this day: (10×16013) depths×nodes
                day_boolean_region = day_boolean_full[:, region_node_indices]  #subset to region nodes: (10×N_region_nodes)
                
                nodes_below_any_depth = day_boolean_region.max(axis=0)  #for each node, check if ANY depth is below threshold: (N_region_nodes,) boolean array
                
                daily_areas[day_idx] = (region_areas_m2[nodes_below_any_depth].sum()) * 1e-6  #sum area of nodes below threshold, convert m² to km²
            
            daily_area_results[threshold_key][run_type][region] = daily_areas  #store 361-day array for this threshold/scenario/region combination
            
            print(f"    {threshold_key} - {run_type} - {region}: Max daily area = {daily_areas.max():.3f} km²")  #show maximum daily area as verification

print("Daily area extraction complete.")

# ==============================================================================
# Area Sec. 3: Area Statistics Function
# ==============================================================================
# Create statistics DataFrames for area (copied from volume statistics function)
# Calculates min/max/avg daily areas and their percentages of total regional area
# Returns two DataFrames ready for Excel export (one for existing, one for reference scenario)

def create_area_statistics_dataframes(threshold_key, regions_to_plot, regional_total_areas=None):
    """
    Create DataFrames for daily area statistics - ready for Excel export
    Parallel to create_volume_statistics_dataframes but for area metrics
    
    Parameters:
    threshold_key: which threshold to analyze (e.g., 'threshold_2')  
    regions_to_plot: list of regions to include in output
    regional_total_areas: dict with total area for each region in km²
    
    Returns:
    df_existing, df_reference: DataFrames formatted for Excel export with area statistics
    """
    
    # Using scenarios, scenario_labels initialized at beginning of script workflow

    dataframes = {}  #store DataFrames for each scenario

    for scenario in scenarios:  # Loops: 'wqm_baseline', then 'wqm_reference'
        table_data = []  #initialize list to store row data
        
        for region in regions_to_plot:  #iterate through regions to include in table
            data = daily_area_results[threshold_key][scenario][region]  #get 361-day array of daily areas for this combination
            
            min_idx = np.argmin(data)  #find day index with minimum area below threshold
            max_idx = np.argmax(data)  #find day index with maximum area below threshold
            min_date = time_coords[min_idx].strftime('%m/%d')  #convert index to date string MM/DD
            max_date = time_coords[max_idx].strftime('%m/%d')  #convert index to date string MM/DD
            
            min_area = data.min()  #minimum daily area (km²) across 361 days
            avg_area = data.mean()  #average daily area (km²) across 361 days
            max_area = data.max()  #maximum daily area (km²) across 361 days - worst case single day

            total_region_area = regional_total_areas.get(region, None) if regional_total_areas else None  #get total area for percentage calculations
            avg_area_pct = (avg_area / total_region_area) * 100 if total_region_area else None  #average as percentage of total regional area
            min_area_pct = (min_area / total_region_area) * 100 if total_region_area else None  #minimum as percentage of total
            max_area_pct = (max_area / total_region_area) * 100 if total_region_area else None  #maximum as percentage of total

            #Calculate habitat area (nodes with ANY valid depth layer in habitat mask)
            # Check which nodes in region have at least one non-NaN depth layer in habitat mask
            region_mask_habitat = (gdf['Regions'] == region) & (gdf['included_i'] == 1) if region != 'All_regions' else (gdf['included_i'] == 1)  #get mask for nodes in this region (for habitat calculation)
            region_indices_habitat = np.where(region_mask_habitat)[0]  #array indices for this region's nodes (for habitat calculation)
            habitat_mask_for_region = habitat_depth_mask[0, :, region_indices_habitat]  #extract habitat mask; shape is (N_region, 10) due to numpy advanced indexing
            nodes_in_habitat = np.any(~np.isnan(habitat_mask_for_region), axis=1)  #check each node: is ANY depth layer valid? axis=1 collapses depths dimension, result is (N_region,) boolean
            habitat_region_area = (gdf.Area_m2.iloc[region_indices_habitat][nodes_in_habitat].sum()) * 1e-6  #select areas of nodes in habitat, sum them, convert m² to km² (×1e-6)

            #Calculate unique area for nodes violated at least once during year
            violations_data = all_threshold_results[threshold_key]['ParmBelowThresh_daily_data'][scenario]  #(361×10×16013) boolean array showing violations per day×depth×node
            region_mask = (gdf['Regions'] == region) & (gdf['included_i'] == 1) if region != 'All_regions' else (gdf['included_i'] == 1)  #get mask for nodes in this region
            region_indices = np.where(region_mask)[0]  #array indices for this region's nodes
            ever_violated_nodes = violations_data.any(axis=0).any(axis=0)[region_indices]  #collapse days & depths to get nodes ever violated
            unique_area = (gdf.Area_m2.iloc[region_indices][ever_violated_nodes].sum()) * 1e-6  #sum areas of violated nodes, convert to km²
            unique_area_pct = (unique_area / total_region_area) * 100 if total_region_area else None  #percentage of total region area
            
            row = [  #construct row with all statistics for this region
                region,
                f"{total_region_area:.3f}" if total_region_area else "N/A",  #total regional area in km²
                f"{habitat_region_area:.3f}" if habitat_region_area else "N/A",  #habitat area column
                f"{avg_area:.6f}",  #average daily area below threshold
                f"{avg_area_pct:.3f}" if avg_area_pct else "N/A",  #average as % of total
                f"{min_area:.6f}",  #minimum daily area
                min_date,  #date of minimum
                f"{min_area_pct:.3f}" if min_area_pct else "N/A",  #minimum as % of total
                f"{max_area:.6f}",  #maximum daily area
                max_date,  #date of maximum
                f"{max_area_pct:.3f}" if max_area_pct else "N/A",  #maximum as % of total
                f"{unique_area:.3f}",  #unique area
                f"{unique_area_pct:.2f}" if unique_area_pct else "N/A"  #unique area percentage
            ]
            table_data.append(row)
        
        columns = [  #define column headers for DataFrame
            'Region', 'Total_Area_km2', 'Total_Habitat_Area_km2', 'Avg_Area_km2', 'AvgArea_%ofTotal',  #includes habitat area column 
            'Min_Area_km2', 'Min_Date_M/D', 'MinArea_%ofTotal',
            'Max_Area_km2', 'Max_Date_M/D', 'MaxArea_%ofTotal',
            'Total_Unique_Area_km2', 'UniqueArea_%ofTotal'  #unique area columns
        ]
        
        df = pd.DataFrame(table_data, columns=columns)  #create DataFrame for this scenario
        dataframes[scenario] = df  #store in dictionary
    
    return dataframes['wqm_baseline'], dataframes['wqm_reference']  #return both DataFrames

# ==============================================================================
# Area Sec. 4: Add Area Tabs to Excel Files
# ==============================================================================
# Add Area_Existing and Area_Reference tabs to existing threshold Excel files
# Reads each threshold Excel file, creates area statistics, inserts new tabs after Number_of_Days
# Preserves all existing tabs (Volume, Percent, README) in original order

def add_area_tabs_to_existing_excels():
    """
    Add Area_Existing and Area_Reference tabs to existing threshold Excel files
    Parallel to add_volume_tabs_to_existing_excels but for area metrics
    Inserts Area tabs immediately after Number_of_Days tab
    """
    
    excel_dir = pathlib.Path(excel_output_path)  #get path to Excel directory
    
    excel_files = list(excel_dir.glob(f'{case}_{scope}_*-lt-*.xlsx'))  #find all threshold Excel files matching pattern
    excel_files = [f for f in excel_files if 'noncompliant' not in f.name]  #exclude noncompliant files (different structure)
    
    print(f"\nAdding Area tabs to {len(excel_files)} Excel files...")
    
    for excel_file in excel_files:  #process each threshold Excel file
        threshold_part = excel_file.stem.split('-lt-')[1]  #extract portion after '-lt-' in filename
        if threshold_part.startswith('DO_standard'):  #handle special case of DO_standard threshold
            threshold_match = 'DO_standard'  #use full name for DO_standard
        else:
            threshold_match = threshold_part.split('_')[0]  #extract threshold number (works for integers and decimals like 0.5, 1.3, etc.)
        threshold_key = f'threshold_{threshold_match}'  #construct dictionary key
        
        if threshold_key not in daily_area_results:  #check if this threshold was processed in daily area extraction
            print(f"  Skipping {excel_file.name} - threshold {threshold_key} not in daily_area_results")
            continue  #skip this file if threshold data not available
        
        print(f"  Processing {excel_file.name}")
        
        df_area_existing, df_area_reference = create_area_statistics_dataframes(  #create area statistics DataFrames for this threshold
            threshold_key, regions, regional_areas)  #pass threshold, region list, and area dictionary
        
        existing_data = {}  #dictionary to store all existing sheets from Excel file
        with pd.ExcelFile(excel_file) as xls:  #open Excel file for reading
            for sheet_name in xls.sheet_names:  #iterate through all existing sheets
                existing_data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)  #read each sheet into dictionary
        
        with pd.ExcelWriter(excel_file, mode='w', engine='openpyxl') as writer:  #open Excel file for writing (overwrites existing)
            if 'Number_of_Days' in existing_data:  #write Number_of_Days tab first if it exists
                existing_data['Number_of_Days'].to_excel(writer, sheet_name='Number_of_Days', index=False)
            
            df_area_existing.to_excel(writer, sheet_name='Area_Existing', index=False)  #write Area_Existing tab (new)
            df_area_reference.to_excel(writer, sheet_name='Area_Reference', index=False)  #write Area_Reference tab (new)
            
            for sheet_name, data in existing_data.items():  #write all remaining existing tabs
                if sheet_name != 'Number_of_Days':  #skip Number_of_Days since already written
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"    Added Area_Existing and Area_Reference tabs after Number_of_Days in {excel_file.name}")

add_area_tabs_to_existing_excels()  #execute function to add area tabs to all threshold Excel files

print("\n=== AREA PROCESSING COMPLETE ===")


# ============================================================================
# ## Node statistics to excel tables (avg min and max)-adds tabs to existing excel:
# ============================================================================

# ==============================================================================
# NODE ANALYSIS - COMPLETE PROCESSING BLOCK
# ==============================================================================
# This block adds Node count analysis parallel to Volume and Area analysis
# Counts number of model grid cells (nodes) below threshold each day
# Output Excel tabs: Nodes_Existing, Nodes_Reference (same structure as Volume/Area tabs)
# ==============================================================================

# ==============================================================================
# Node Sec. 1: Calculate Regional Total Node Counts from Shapefile
# ==============================================================================
# Calculate total node count for each region from gdf
# Node = model grid cell; count of nodes = count of spatial locations in region

print("Calculating regional total node counts from shapefile...")
regional_node_counts = {}  #initialize dictionary to store total node count (integer) for each region
for region in regions:  #iterate through all regions including All_regions
    if region == 'All_regions':
        idx = (gdf['included_i'] == 1)  #All_regions counts all included nodes across entire domain
        regional_node_counts[region] = idx.sum()  #sum True values in boolean mask = count of nodes
    else:
        idx = (gdf['Regions'] == region) & (gdf['included_i'] == 1)  #individual region filters by region name and included status
        regional_node_counts[region] = idx.sum()  #sum True values = count of nodes in this region

print(f"Regional node counts calculated: {list(regional_node_counts.keys())}")  #show which regions have node count data
print("Sample node counts:", {k: v for k, v in list(regional_node_counts.items())[:3]})  #display first 3 regions as verification

# ==============================================================================
# Node Sec. 2: Daily Node Extraction Loop
# ==============================================================================
# Extract daily node counts below threshold for each region/scenario
# For each day, counts how many nodes have ANY depth below threshold
# Reuses existing node statistics code pattern - stores results instead of just printing

print("\n=== Starting Daily Node Extraction ===")
daily_node_results = {}  #initialize nested dictionary: daily_node_results[threshold][scenario][region] = 361-day array of daily node counts (integers)

for threshold_key in all_threshold_results.keys():  #iterate through all thresholds (threshold_1, threshold_2, threshold_5, threshold_DO_standard, etc.)
    print(f"Processing {threshold_key}...")
    
    daily_boolean_full = all_threshold_results[threshold_key]['ParmBelowThresh_daily_data']  #dict with (361×10×16013) boolean arrays where True = below threshold
    
    daily_node_results[threshold_key] = {}  #initialize scenario level for this threshold
    
    for run_type in daily_boolean_full.keys():  #iterate through scenarios: 'wqm_baseline', 'wqm_reference'
        print(f"  {threshold_key} - {run_type}: Starting daily node count calculation")
        
        daily_boolean_scenario = daily_boolean_full[run_type]  #extract (361×10×16013) boolean array for current scenario
        daily_node_results[threshold_key][run_type] = {}  #initialize region level for this scenario
        
        for region in regions:  #iterate through each region including All_regions
            if region == 'All_regions':
                region_mask = (gdf['included_i'] == 1)  #All_regions uses all included nodes
            else:
                region_mask = (gdf['Regions'] == region) & (gdf['included_i'] == 1)  #individual region filters by region name and included status
            
            region_node_indices = np.where(region_mask)[0]  #get array indices of nodes in this region
            
            daily_node_counts = []  #initialize list to store node count for each of 361 days
            for day_idx in range(361):  #loop through each day of the year
                day_boolean_full = daily_boolean_scenario[day_idx, :, :]  #extract boolean for this day: (10×16013) depths×nodes
                region_boolean = day_boolean_full[:, region_node_indices]  #subset to region nodes: (10×N_region_nodes)
                
                nodes_below_threshold = region_boolean.max(axis=0).sum()  #for each node, check if ANY depth is below threshold, then count how many nodes qualify
                daily_node_counts.append(nodes_below_threshold)  #store daily count in list
            
            daily_node_counts = np.array(daily_node_counts)  #convert list to numpy array for statistics: (361,) array of daily node counts
            daily_node_results[threshold_key][run_type][region] = daily_node_counts  #store 361-day array for this threshold/scenario/region combination
            
            print(f"    {threshold_key} - {run_type} - {region}: Max daily nodes = {daily_node_counts.max()}")  #show maximum daily node count as verification

print("Daily node extraction complete.")

# ==============================================================================
# Node Sec. 3: Node Statistics Function
# ==============================================================================
# Create statistics DataFrames for node counts (copied from area statistics function)
# Calculates min/max/avg daily node counts and their percentages of total regional nodes
# Returns two DataFrames ready for Excel export (one for existing, one for reference scenario)

def create_node_statistics_dataframes(threshold_key, regions_to_plot, regional_total_node_counts=None):
    """
    Create DataFrames for daily node count statistics - ready for Excel export
    Parallel to create_area_statistics_dataframes but for node count metrics
    
    Parameters:
    threshold_key: which threshold to analyze (e.g., 'threshold_2')  
    regions_to_plot: list of regions to include in output
    regional_total_node_counts: dict with total node count for each region (integers)
    
    Returns:
    df_existing, df_reference: DataFrames formatted for Excel export with node statistics
    """
    
    # Using scenarios, scenario_labels initialized at beginning of script workflow

    dataframes = {}  #store DataFrames for each scenario

    for scenario in scenarios:  # Loops: 'wqm_baseline', then 'wqm_reference'
        table_data = []  #initialize list to store row data
        
        for region in regions_to_plot:  #iterate through regions to include in table
            data = daily_node_results[threshold_key][scenario][region]  #get 361-day array of daily node counts for this combination
            
            min_idx = np.argmin(data)  #find day index with minimum node count
            max_idx = np.argmax(data)  #find day index with maximum node count
            min_date = time_coords[min_idx].strftime('%m/%d')  #convert index to date string MM/DD
            max_date = time_coords[max_idx].strftime('%m/%d')  #convert index to date string MM/DD
            
            min_nodes = int(data.min())  #minimum daily node count (integer) across 361 days
            avg_nodes = data.mean()  #average daily node count (decimal) across 361 days
            max_nodes = int(data.max())  #maximum daily node count (integer) across 361 days - worst case single day
            
            total_region_nodes = regional_total_node_counts.get(region, None) if regional_total_node_counts else None  #get total nodes for percentage calculations
            avg_nodes_pct = (avg_nodes / total_region_nodes) * 100 if total_region_nodes else None  #average as percentage of total regional nodes
            min_nodes_pct = (min_nodes / total_region_nodes) * 100 if total_region_nodes else None  #minimum as percentage of total
            max_nodes_pct = (max_nodes / total_region_nodes) * 100 if total_region_nodes else None  #maximum as percentage of total

            #Calculate habitat node count (nodes with ANY valid depth layer in habitat mask)
            region_mask_habitat = (gdf['Regions'] == region) & (gdf['included_i'] == 1) if region != 'All_regions' else (gdf['included_i'] == 1)  #get mask for nodes in this region (for habitat calculation)
            region_indices_habitat = np.where(region_mask_habitat)[0]  #array indices for this region's nodes (for habitat calculation)
            habitat_mask_for_region = habitat_depth_mask[0, :, region_indices_habitat]  #extract habitat mask; shape is (N_region, 10) due to numpy advanced indexing
            nodes_in_habitat = np.any(~np.isnan(habitat_mask_for_region), axis=1)  #boolean array: True if node has ANY non-NaN depth; axis=1 collapses depth dimension
            habitat_region_nodes = nodes_in_habitat.sum()  #count True values = number of nodes in habitat

            #Calculate unique nodes violated at least once during year
            violations_data = all_threshold_results[threshold_key]['ParmBelowThresh_daily_data'][scenario]  #(361×10×16013) boolean array showing violations per day×depth×node
            region_mask = (gdf['Regions'] == region) & (gdf['included_i'] == 1) if region != 'All_regions' else (gdf['included_i'] == 1)  #get mask for nodes in this region
            region_indices = np.where(region_mask)[0]  #array indices for this region's nodes
            ever_violated_nodes = violations_data.any(axis=0).any(axis=0)[region_indices]  #collapse days & depths to get nodes ever violated
            unique_nodes = ever_violated_nodes.sum()  #count of True values for unique nodes
            unique_nodes_pct = (unique_nodes / total_region_nodes) * 100 if total_region_nodes else None  #percentage of total region nodes
            
            row = [  #construct row with all statistics for this region
                region,
                total_region_nodes,  #total nodes in region (integer)
                habitat_region_nodes,  #habitat nodes count
                f"{avg_nodes:.1f}",  #average daily nodes below threshold (decimal)
                f"{avg_nodes_pct:.2f}" if avg_nodes_pct else "N/A",  #average as % of total
                min_nodes,  #minimum daily nodes (integer)
                min_date,  #date of minimum
                f"{min_nodes_pct:.2f}" if min_nodes_pct else "N/A",  #minimum as % of total
                max_nodes,  #maximum daily nodes (integer)
                max_date,  #date of maximum
                f"{max_nodes_pct:.2f}" if max_nodes_pct else "N/A",  #maximum as % of total
                unique_nodes,  #unique nodes
                f"{unique_nodes_pct:.2f}" if unique_nodes_pct else "N/A"  #unique nodes percentage
            ]
            table_data.append(row)
        
        columns = [  #define column headers for DataFrame
            'Region', 'Total_Nodes', 'Total_Habitat_Nodes', 'Avg_Nodes', 'AvgNodes_%ofTotal',  #includes habitat nodes column 
            'Min_Nodes', 'Min_Date_M/D', 'MinNodes_%ofTotal',
            'Max_Nodes', 'Max_Date_M/D', 'MaxNodes_%ofTotal',
            'Total_Unique_Nodes', 'UniqueNodes_%ofTotal'  #unique nodes columns
        ]
        
        df = pd.DataFrame(table_data, columns=columns)  #create DataFrame for this scenario
        dataframes[scenario] = df  #store in dictionary
    
    return dataframes['wqm_baseline'], dataframes['wqm_reference']  #return both DataFrames

# ==============================================================================
# Node Sec. 4: Add Node Tabs to Excel Files
# ==============================================================================
# Add Nodes_Existing and Nodes_Reference tabs to existing threshold Excel files
# Reads each threshold Excel file, creates node statistics, inserts new tabs after Area tabs
# Preserves all existing tabs (Volume, Area, Percent, README) in original order

def add_node_tabs_to_existing_excels():
    """
    Add Nodes_Existing and Nodes_Reference tabs to existing threshold Excel files
    Parallel to add_area_tabs_to_existing_excels but for node count metrics
    Inserts Node tabs after Area tabs (or after Number_of_Days if no Area tabs)
    """
    
    excel_dir = pathlib.Path(excel_output_path)  #get path to Excel directory
    
    excel_files = list(excel_dir.glob(f'{case}_{scope}_*-lt-*.xlsx'))  #find all threshold Excel files matching pattern
    excel_files = [f for f in excel_files if 'noncompliant' not in f.name]  #exclude noncompliant files (different structure)
    
    print(f"\nAdding Node tabs to {len(excel_files)} Excel files...")
    
    for excel_file in excel_files:  #process each threshold Excel file
        threshold_part = excel_file.stem.split('-lt-')[1]  #extract portion after '-lt-' in filename
        if threshold_part.startswith('DO_standard'):  #handle special case of DO_standard threshold
            threshold_match = 'DO_standard'  #use full name for DO_standard
        else:
            threshold_match = threshold_part.split('_')[0]  #extract threshold number (works for integers and decimals like 0.5, 1.3, etc.)
        threshold_key = f'threshold_{threshold_match}'  #construct dictionary key
        
        if threshold_key not in daily_node_results:  #check if this threshold was processed in daily node extraction
            print(f"  Skipping {excel_file.name} - threshold {threshold_key} not in daily_node_results")
            continue  #skip this file if threshold data not available
        
        print(f"  Processing {excel_file.name}")
        
        df_node_existing, df_node_reference = create_node_statistics_dataframes(  #create node statistics DataFrames for this threshold
            threshold_key, regions, regional_node_counts)  #pass threshold, region list, and node count dictionary
        
        existing_data = {}  #dictionary to store all existing sheets from Excel file
        with pd.ExcelFile(excel_file) as xls:  #open Excel file for reading
            for sheet_name in xls.sheet_names:  #iterate through all existing sheets
                existing_data[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name)  #read each sheet into dictionary
        
        with pd.ExcelWriter(excel_file, mode='w', engine='openpyxl') as writer:  #open Excel file for writing (overwrites existing)
            if 'Number_of_Days' in existing_data:  #write Number_of_Days tab first if it exists
                existing_data['Number_of_Days'].to_excel(writer, sheet_name='Number_of_Days', index=False)
            
            if 'Area_Existing' in existing_data:  #write Area tabs if they exist
                existing_data['Area_Existing'].to_excel(writer, sheet_name='Area_Existing', index=False)
            if 'Area_Reference' in existing_data:
                existing_data['Area_Reference'].to_excel(writer, sheet_name='Area_Reference', index=False)
            
            df_node_existing.to_excel(writer, sheet_name='Nodes_Existing', index=False)  #write Nodes_Existing tab (new)
            df_node_reference.to_excel(writer, sheet_name='Nodes_Reference', index=False)  #write Nodes_Reference tab (new)
            
            for sheet_name, data in existing_data.items():  #write all remaining existing tabs
                if sheet_name not in ['Number_of_Days', 'Area_Existing', 'Area_Reference']:  #skip already written tabs
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"    Added Nodes_Existing and Nodes_Reference tabs after Area tabs in {excel_file.name}")

add_node_tabs_to_existing_excels()  #execute function to add node tabs to all threshold Excel files

print("\n=== NODE PROCESSING COMPLETE ===")

