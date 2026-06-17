#!/usr/bin/env python
"""
Initialize and Load NetCDF Configuration - Crab 80m Habitat
Module 1 of 14 in the analysis pipeline
"""

# ============================================================================
# MODULE DOCUMENTATION: Metabolic Index Analysis Pipeline
# ============================================================================
#
# **Purpose:** Analyzes metabolic index (or dissolved oxygen) data to assess
# marine habitat suitability using threshold-based calculations with species-specific
# depth limits and habitat constraints.
#
# **Current Configuration:** Crab - 80m depth limit, bottom layer only
#
# ============================================================================
# KEY CONFIGURATION VARIABLES (Required for species variants)
# ============================================================================
#
# **Must Define in Code:**
# - `taxa` = Species selection ("crab", "sole", "salmon") - controls data loading and filenames
# - `scope` = Analysis extent ("wc" for water column, "benthic" for bottom layer)
#       NOTE: In 3D application, "benthic" extracts bottom layer [:, -1, :] from 3D data
# - `case` = Region name ("whidbey", "main", etc.) - used in output filenames
# - `thresholds_to_run` = List of thresholds (e.g., [1, 2] for MI, [2, 5, "DO_standard"] for DO)
#
# **Output Paths (Auto-created):**
# - Base: `SSM_output_path` (e.g., '../../../../SSM_output')
# - Excel: `{SSM_output_path}/SSMspreadsheets/` - NOTE: Overwrites existing files
# - Plots: `{SSM_output_path}/{case}_{scope}_{variable}/`
#
# **File Naming:**
# - Excel: `{case}_{scope}_{variable}-lt-{threshold}_{scenarios}.xlsx`
# - Example: `whidbey_wc_Mindex_crab_routine-lt-2_wqm-baseline-wqm-reference.xlsx`
#
# ============================================================================
# PIPELINE STRUCTURE AND DATA FLOW
# ============================================================================
#
# Module 1: Initialize and Load (THIS MODULE)
#   Functions:
#   - load_all_nc_datasets() → Loads 3D NetCDF data into SSMcalcs_dic dictionary
#   - create_species_habitat_mask_standard_grid_structure() → Creates depth-based habitat mask
#   Output: SSMcalcs_dic with raw data, habitat mask definition, regional boundaries
#
# Module 2a: Apply Habitat Masks
#   - Multiplies SSMcalcs_dic data by habitat_depth_mask → adds NaN where habitat excluded
#   - Creates volume2D_masked = volume2D * habitat_depth_mask
#   Output: Masked data arrays with NaN outside habitat zones
#
# Module 2b: Calculate Regional Volumes
#   - Calculates regional_volumes_WC (full water column) for each region
#   - Calculates regional_volumes (habitat-masked volumes)
#   Output: Volume dictionaries by region for denominators
#
# Module 2c: Add NetCDF Attributes
#   - Adds long_name and units attributes to all variables in SSMcalcs_dic
#   - Example: 'DOX' gets 'Dissolved Oxygen' and 'mg/L'
#   Output: Enhanced metadata for plotting and exports
#
# Module 2d: Prepare Threshold Input Data
#   - Extracts data from SSMcalcs_dic into ssm_input_datasets format
#   - Prepares existing/reference scenario comparison structure
#   Output: ssm_input_datasets dictionary for threshold analysis
#
# Module 3a: Calculate Thresholds & Create Excel
#   Functions:
#   - calc_DO_below_thresh() → Main threshold exceedance calculations
#   - Creates initial Excel with 3 tabs: Number_of_Days, Volume_Days, Percent_Volume_Days
#   Output: Excel files named {case}_{scope}_{variable}-lt-{threshold}_{scenarios}.xlsx
#
# Module 3b: Plot Timeseries Volumes
#   Functions:
#   - plot_daily_threshold_volumes() → Creates multi-panel time series plots by region
#   - Shows daily volume below threshold over 361 days
#   Output: PNG plots of temporal patterns
#
# Module 3c: Plot Stacked Volumes
#   Functions:
#   - plot_multi_threshold_stacked_volumes() → Creates stacked area plots
#   - Shows cumulative volumes across thresholds
#   Output: Stacked visualization PNG files
#
# Module 4a: Create Volume Statistics & Add to Excel
#   Functions:
#   - create_volume_statistics_dataframes() → Calculates min/max/avg/unique volumes
#   - add_volume_tabs_to_existing_excels() → Adds Volume_Existing and Volume_Reference tabs
#   Adds to Excel: Two new tabs with daily volume statistics including habitat denominators
#
# Module 4b: Create Pivot Summary Excel
#   Functions:
#   - create_threshold_summary_table() → Creates pivot tables of volume percentages
#   - export_volume_summary_excel() → Exports separate summary file
#   Output: New Excel {case}_{scope}_{variable}_volume_percent_all_thresh_summary.xlsx
#
# Module 4c: Create Area/Node Statistics & Add to Excel
#   Functions:
#   - create_area_statistics_dataframes() → Calculates area metrics (km²)
#   - create_node_statistics_dataframes() → Counts affected nodes
#   - add_area_tabs_to_existing_excels() → Adds Area_Existing and Area_Reference tabs
#   - add_node_tabs_to_existing_excels() → Adds Nodes_Existing and Nodes_Reference tabs
#   Adds to Excel: Four new tabs (2 for area, 2 for nodes) with statistics
#
# ============================================================================
# KEY OUTPUTS AND METRICS
# ============================================================================
#
# Excel Structure (per threshold):
#   Original tabs (from 3a):
#   - Number_of_Days: Count of days exceeding threshold by region
#   - Volume_Days: Cumulative volume×days below threshold (km³·days)
#   - Percent_Volume_Days: As percentage of regional volume×361 days
#   - README: Documentation of calculations and denominators
#
#   Added tabs (from 4a):
#   - Volume_Existing: Daily statistics with Total_Vol and Total_Habitat_Vol columns
#   - Volume_Reference: Same structure for reference scenario
#
#   Added tabs (from 4c):
#   - Area_Existing: Daily area statistics with Total_Area and Total_Habitat_Area
#   - Area_Reference: Same for reference scenario
#   - Nodes_Existing: Node count statistics with Total_Nodes and Total_Habitat_Nodes
#   - Nodes_Reference: Same for reference scenario
#
# Denominator Note:
#   All metrics provide two denominators:
#   - Total_[metric]: Full water column extent (no masking)
#   - Total_Habitat_[metric]: Habitat-masked extent only
#   Current %ofTotal uses Total column; see README for %ofHabitat formulas
#
# ============================================================================


# ============================================================================
# OLD DOCUMENTATION BELOW - TO BE REVIEWED AND REMOVED
# ============================================================================
# 2025.11.04 Mazzilli  Volume days by region code adapted from Rachael M code (see PSI repository)
# 3D (or selects benthic bottom layer) Water Column non-compliance and below threhold analysis by region for for volume days -either DO or Metabolic index results
#   added a maximum volume days extaction by region
#see changes need below for specific runs:
# This specific run is for: DO min (max commented out) analysis with thresholds 2, 5, and DO_standard
# removed metabolic load eg  # SSMcalcs_dic.update(metabolic_datasets)

#all relative inputs and outputs for hyak/local run -will work on hyak on either ecy 2025 (last usedfor this) or Ahmed 2021 PSIdata

# to change DO/MIndex and to choose with or without "other" region see  specfic outputs toggle key places below on "to switch" in description below 

#currently masking Nans to exclude all but bottom layer (crab) AND for *_exsit/ref tabs and plots to take "regional total volume" specificially from masked result not regions directly from shapefle
#working for MI export without multthrehsold plot steps tstill to do:
#1) add multthshold
#2) add depth mask dynamic



# ============================================================================
# ## OLD Description - REVIEW FOR RELEVANT NOTES
# ============================================================================


# ============================================================================
# **Purpose:** Analyzes dissolved oxygen or metabolic index data to assess marine habitat suitability using threshold-based risk calculations and regulatory non-compliance metrics. 
# 
# ### Input Requirements (must define in initalize andload section) e.g.:
# 
# - **Data Directories**: 
#   - `NetCDF_input_dir` - Path to NetCDF files containing 3D oceanographic data orr Metabolic
# - **Configuration**: 
#   - `../../etc/SSM_config_metabolic.yaml` - Analysis parameters and run definitions
#   - Shapefile path for regional boundaries
# - **User Settings**:
#   - `taxa` - Species selection ("crab", "sole", "salmon")  
#   - `scope` - Analysis extent ("wc" for water column, "benthic" for bottom layer) NOTE see further details on"scope" below in this 3d application using WC only
#   - `case` - Region name ("whidbey", "main", etc.)
# 
# ### Output Directories (must define in initalize andload section) e.g.:
# - **base output dir for below**: `SSM_output_path` 
# - **Excel Files**: `/SSMspreadsheets/` subdirectory under graphics path from config (dynamic)
# - **Plots**: `/output_excel_dir/` - Timeseries plot directory (dynamic based on base output)
# - **File Naming e.g.**: `{case}_{scope}_{variable}-lt-{threshold}_{scenarios}.xlsx`
# 
# ### Core Functions:
# 
# - **`load_all_nc_datasets()`**: Loads 3D oceanographic data from NetCDF files
#   - Handles both DO data (`MinParam_WholeYear10Layers_timeseries_DOX`) and metabolic index data (`CalMinParam_3D_{taxa}_Mindex_routine`)
#   - Supports existing and reference scenarios for comparison
# 
# - **`calc_DO_below_thresh()`**: Threshold exceedance analysis 
#   - Calculates days/volume below specified thresholds (2, 5 mg/L for DO; 1, 2 for metabolic index)
#   - Supports `DO_standard` input for variable thresholds by region
#   - Regional statistics aggregated by Puget Sound boundaries
#   - Excel export with volume-days and percent volume affected
# 
# - **`calc_noncompliant()`**: Regulatory non-compliance analysis (**DO-specific only**)
#   - Uses human allowance (`-0.2 mg/L`) and non-compliant threshold (`-0.25 mg/L`) parameters
#   - Calculates existing vs reference scenario differences
#   - Applies DO standard + human allowance criteria for Part B non-compliance
#   - Regional and domain-wide compliance statistics
# 
# ### Data Processing Options:
# - **Scope Selection**: Full water column (`scope = 'wc'`) or bottom layer (`scope = 'benthic'`)
# - **Dynamic Taxa**: Uses `taxa` variable for species-specific metabolic index analysis
# - **Regional Analysis**: Aggregates by Puget Sound regions using shapefile boundaries
# 
# ### Key Outputs:
# - **Threshold Files**: `{case eg whidbey}_{scope eg wc}_{variable eg Mindex}-lt-{threshold eg 1}_{scenarios eg wqm_baseline (existing)}.xlsx`
# - **Non-compliance Files**: `{case}_wc_noncompliant_{threshold}.xlsx` (DO only)
# 
# ### To Switch Between DO and Metabolic Index Analysis - Toggle inputs in two sections 
# 
# **Initialize Section Configuration**: Look for the initialization section at the top for these key settings and toggle:
# - **Data Source Path**: `directory_path = ` - Update path to your data location
# - **Analysis Type**: `scope = ` - Set to `"wc"` (water column) or `"benthic"` (bottom layer)  
# - **Thresholds**: `thresholds_to_run = [` - Use metabolic values (1,2) or DO values (2,5, "DO_standard")
# - **Species Selection (metabolic index only)**: `taxa = ` - Choose "crab", "sole", or "salmon" for metabolic index analysis
# 
# **Data Mapping Section - Toggle Each Analysis**:
# - **Search for**: `existing_data = SSMcalcs_dic[` and `variable_name =`
# - **For DO**: Use `'MinParam_WholeYear10Layers_timeseries_DOX'` and `'DOXG_daily_min_wc'`
# - **For Metabolic Index**: Use `f'CalMinParam_3D_{taxa}_Mindex_routine'` and `f'Mindex_{taxa}_routine'`
# 
# **Plot time series for each threshold and multilayer plot**:
# - toggle lines for plot headings for each (2x locations) 
# - toggle legend on  multilayer search DO Range
# 
# **Automatic Features**:
# - **Scope* Processing**: `scope = "benthic"` automatically extracts bottom layer `[:, -1, :]` from 3D data- NOTE: Code change from original which took the 2d data layer. Will not take 2d currently 
# - **Filename Detection**: `excel_file_param_name = variable_name` automatically creates appropriate filenames
# - **Non-compliance Analysis**: Only available for DO analysis, comment out for metabolic index
# 
# **Note on functions and denominator in metrics
# - ** Non-compliance analysis with regulatory thresholds only applies to dissolved oxygen data.
# - ** All numerator metrics (Min/Avg/Max/Unique volumes, areas, nodes, Volume_Days) are habitat-filtered via NaN masking. Two denominators provided: Total (full WC) 
#      and Total_Habitat (habitat only). Percent_Volume_Days uses full WC denominator.
#      For %ofHabitat calculations, use README formulas. Relevant for MI with habitat mask NOT DO
# 
# ### Regions -To Switch Between including "other" region in analysis and excel and in plots : 
# - functions and excel outputs:  3x regions.remove('Other') toggle and comment off  to include other by default
# - plots:  toggle off 3x regions = ['All_regions', .... which specifiy other , in three  locations where the order and exclusion of specific regions is defined for each plot
# - plots will then use default regional names which will include other as not removed  in functions earlier 
# ============================================================================


# ============================================================================
# ## Logic flow and processing pathway: DO/MI Analysis Flow (Multiple Functions)
# 
# **Note:** Despite the name, `calc_DO_below_thresh()` is used for BOTH DO and Metabolic Index analysis. The downstream daily volume functions add additional tabs with correct denominators, but the core `Percent_Volume_Days` tab from `calc_DO_below_thresh()` has the wrong denominator when habitat masking is applied.
# ```
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  DO/MI ANALYSIS PATHWAY (spans multiple functions/sections)             │
# ├─────────────────────────────────────────────────────────────────────────┤
# │                                                                         │
# │  ┌───────────────────────────────────────────────────────────────────┐  │
# │  │ MAIN SCRIPT - Data Loading & Masking Section                      │  │
# │  ├───────────────────────────────────────────────────────────────────┤  │
# │  │                                                                   │  │
# │  │  1. Load DO or MI data into SSMcalcs_dic                          │  │
# │  │                    ↓                                              │  │
# │  │  2. habitat_depth_mask applied to SSMcalcs_dic                    │  │
# │  │     Search: "SSMcalcs_dic[dataset_key][scenario_key][var_name]    │  │
# │  │              .values *= habitat_depth_mask"                       │  │
# │  │     → Data values get NaN where mask is NaN ✓                     │  │
# │  │                    ↓                                              │  │
# │  │  3. volume2D_masked and regional_volumes calculated               │  │
# │  │     Search: "volume2D_masked = volume2D * habitat_depth_mask"     │  │
# │  │     Search: "regional_volumes = effective_regional_volumes"       │  │
# │  │     → Correct habitat-masked volumes available ✓                  │  │
# │  │                    ↓                                              │  │
# │  │  4. Extract to ssm_input_datasets                                 │  │
# │  │     Search: "ssm_input_datasets = {"                              │  │
# │  │     → Data passed to function HAS NaN from mask ✓                 │  │
# │  │                                                                   │  │
# │  └───────────────────────────────────────────────────────────────────┘  │
# │                    ↓                                                    │
# │  ┌───────────────────────────────────────────────────────────────────┐  │
# │  │ FUNCTION: calc_DO_below_thresh()                                  │  │
# │  ├───────────────────────────────────────────────────────────────────┤  │
# │  │                                                                   │  │
# │  │  5. Function called with ssm_input_datasets                       │  │
# │  │     Search: "results_threshold = calc_DO_below_thresh("           │  │
# │  │     → Function INTERNALLY recalculates volume2D from shapefile:   │  │
# │  │       "volume2D = np.dot(volume.reshape(nnodes, 1),"              │  │
# │  │     → Uses FULL WC volume, NOT habitat-masked volume ✗            │  │
# │  │     → Percent_Volume_Days denominator = Full WC × 361 days ✗      │  │
# │  │                    ↓                                              │  │
# │  │  6. Excel output written inside function                          │  │
# │  │     Search: "with pandas.ExcelWriter("..."-lt-{thresh_filename}"  │  │
# │  │     → Number_of_Days tab: correct (count, no denominator)         │  │
# │  │     → Volume_Days tab: data is masked, raw km³·days ✓             │  │
# │  │     → Percent_Volume_Days tab: WRONG DENOMINATOR ✗                │  │
# │  │                                                                   │  │
# │  └───────────────────────────────────────────────────────────────────┘  │
# │                    ↓                                                    │
# │  ┌───────────────────────────────────────────────────────────────────┐  │
# │  │ MAIN SCRIPT - Daily Volume Analysis Section                       │  │
# │  ├───────────────────────────────────────────────────────────────────┤  │
# │  │                                                                   │  │
# │  │  7. Daily volume analysis runs AFTER calc_DO_below_thresh         │  │
# │  │     Search: "daily_volume_results[threshold_key][run_type]"       │  │
# │  │     → Uses regional_volumes (habitat-masked) for calculations ✓   │  │
# │  │                                                                   │  │
# │  └───────────────────────────────────────────────────────────────────┘  │
# │                    ↓                                                    │
# │  ┌───────────────────────────────────────────────────────────────────┐  │
# │  │ FUNCTION: add_volume_tabs_to_existing_excels()                    │  │
# │  ├───────────────────────────────────────────────────────────────────┤  │
# │  │                                                                   │  │
# │  │  8. Adds new tabs to Excel files created in step 6                │  │
# │  │     Search: "def add_volume_tabs_to_existing_excels():"           │  │
# │  │     → Volume_Existing/Reference tabs with correct % ✓             │  │
# │  │     → Uses regional_volumes as denominator ✓                      │  │
# │  │                                                                   │  │
# │  └───────────────────────────────────────────────────────────────────┘  │
# │                                                                         │
# │  RESULT: Percent_Volume_Days tab has wrong denominator                  │
# │          Volume_Existing/Reference tabs have correct denominator        │
# │          BUT these come from separate downstream calculation            │
# └─────────────────────────────────────────────────────────────────────────┘


# ============================================================================
# ## Initialize and Load V3 Data Structure
# ============================================================================

#initalize toggling inputs and key parameters for DO vs specific species metabolic index
import os
import sys
import xarray
import openpyxl
import contextily as cx 
import numpy as np
import pandas
import pathlib
from datetime import date
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
#non compliance specific:
from helper_variable_name_datasetreview import clean_shapefile_check16012_len  #shapefile cleaning function
import os  #for directory operations
import pathlib  #for path operations
import time  #for execution timing
from ssm_utils import calculate_ssm_layer_positive_depths_m  #Import SSM depth calculation function


# ============================================================================
# ## Metabolic Index and Habitat Mask Configuration
# ============================================================================
# Species depth limit (meters)
species_depth_limit_m = 80  # Set to 80 for crab, 200 for salmon, 10000 for no depth filtering (10000m adds no NaNs)


#depth selection for processing to match input data:
scope = "wc"  # FIXED VARIABLE:  earlier version  either - 'wc' for water column (3d), 'benthic' for bottom layer (2d) new code added to select bottom layer from 3d data
#In advanced code scope='bc' is NOT SUPPORTED as it expects 2D data incompatible with 3D habitat masking. # Layer filtering eg for crab and bottom layer is controlled dynamically by layer_filter_mode, NOT scope.
case = 'whidbey'  # FIXED VARIABLE: prior code has region case name - can be 'whidbey', 'main', 'SOG_NB', etc. not implemented in advanceed code here

# Layer filtering mode - controls which layers to keep vs NaN out
# Options: 'bottom_only', 'surface_only', 'top_3', 'all_layers'
# To edit layer ranges, search for "layer_filter_mode ==" in 2a_manipulate_habitat_depth_masks.py
layer_filter_mode = 'bottom_only'  # Change this to control layer filtering (edit in 1_initialize_load_netcdf_config.py)
#layer_filter_mode = 'all_layers' # whole water column (wc)

#thresholds_to_run = [2, 5, "DO_standard"] #DO selected thresholds for DEBUG and QA which does not complete all plots/spreadsheets
#thresholds_to_run = [0.00001,1,2,3,4,5,6,7,10,14,1000, "DO_standard"] #DO all thresholds for plots 
thresholds_to_run = [0.00001,0.25,0.5,0.75,1,1.25,1.5,1.75,2,7,10,1000, "DO_standard"] #MI thresholds for plots 

#Metabolic index specific #Set taxa for file naming and processing (Separate DO procssing and will not affect file name produced for DO or other)
#taxa = "salmon"  #Taxa name for file naming and processing
taxa = "crab" 
#taxa = "sculpin"  
#taxa = "sole"

# Shapefile and regions:
#NOTE: Plots: Regions set manually currently for plots, see and uncomment regions = regions to use dynamic load and naming in def plot_daily_volumes_simple (3b_plot_timeseries_threshold_volumes.py)

# ==============================================================================
# MODEL SCENARIO CONFIGURATION - Centralized definitions
# ==============================================================================
# Define all scenarios in one place for consistency across scripts

# Scenario list (used in: plot_daily_threshold_volumes() in 3b_plot, add_volume_tabs_to_existing_excels() in 4a_volume, 4c_area_node multiple functions)
scenarios = ['wqm_baseline', 'wqm_reference']
# scenarios = ['wqm_baseline', 'wqm_reference', 'future_2050']  # Example with additional scenario

# Display labels (used in: plot_daily_threshold_volumes() in 3b_plot, add_volume_tabs_to_existing_excels() in 4a_volume)
scenario_labels = {
    'wqm_baseline': '2014 Conditions',
    'wqm_reference': 'Reference',
    # 'future_2050': '2050 Projection',
}

# Plot colors (used in: plot_daily_threshold_volumes() in 3b_plot, plot_multi_threshold_stacked_volumes() in 3c_stacked)
scenario_colors = {
    'wqm_baseline': 'black',
    'wqm_reference': 'gray',
    # 'future_2050': 'blue',
}

# Excel tab names (used in: create_summary_excel() in 4b_pivot_summary)
scenario_excel_tabs = {
    'wqm_baseline': '2014_Conditions',
    'wqm_reference': 'Reference',
    # 'future_2050': '2050_Projection',
}

# NetCDF subdirectory mapping (used in: 2d_prepare_threshold_input_data)
nc_subdir_mapping = {
    'exist': 'wqm_baseline',           # Maps 'exist' folder to 'wqm_baseline'
    'wqm_reference': 'wqm_reference',  # Maps 'wqm_reference' to same name
    # 'future_2050': 'future_2050',
}

# === OUTPUT DIRECTORIES ===
SSM_output_path = 'SSM_output' #base directory for all SSM outputs
output_plots_dir = f'{SSM_output_path}/SSM_plot_timeseries' #all timeseries plot PNG files
os.makedirs(output_plots_dir, exist_ok=True) #create plot directory if needed
excel_output_path = f'{SSM_output_path}/SSMspreadsheets' #all Excel spreadsheet files
os.makedirs(excel_output_path, exist_ok=True) #create Excel directory if needed
#NOTE: DO and metabolic index input directories are specified in data loading section below


# ============================================================================
# Species habitat mask function - masking for a given depth (required here for 2a)
# ============================================================================

#Species habitat mask function -masking for a given depth
  # calls from helper function ssm_utils: calculate_ssm_layer_positive_depths_m()
def create_species_habitat_mask_standard_grid_structure(gdf, species_depth_limit_m, siglev_diff=None):
    """
    Create 3D habitat mask based on species depth limits using standard SSM grid structure.

    This function creates a mask where cells beyond the species' depth limit
    are set to NaN, effectively excluding them from volume/area calculations.

    Args:
        gdf: GeoDataFrame with 'depth' column in kilometers
        species_depth_limit_m: Maximum depth for species in meters
        siglev_diff: Optional custom layer thickness percentages

    Returns:
        mask: 3D array (1, 10, 16012) with 1.0=valid habitat, NaN=excluded

    Species-specific usage:
        - Crab (80m): mask = create_species_habitat_mask_standard_grid_structure(gdf, 80.0)
                      then add: mask[0, 0:9, :] = np.nan  # bottom only
        - Salmon (100m): mask = create_species_habitat_mask_standard_grid_structure(gdf, 100.0)
        - Sole (depth TBD): similar to crab pattern
    """
    n_nodes = len(gdf)

    if n_nodes != 16012:
        print(f"WARNING: Expected 16,012 nodes but found {n_nodes}")
        print("Proceeding with actual node count...")

    n_layers = 10
    mask = np.ones((1, n_layers, n_nodes), dtype=float)

    # Extract seafloor depths (convert km to m)
    total_depths_m = gdf['depth'].values * 1000

    # Check each layer's bottom depth against species limit
    for layer_num in range(1, n_layers + 1):
        # Get depth to bottom of this layer for all nodes
        # Unpack layer depths: (top_fraction, BOTTOM_FRACTION, mid_fraction) - extract bottom for threshold checking
        # Using underscore (_) to ignore top_fraction and mid_fraction values we don't need
        _, bottom_frac, _ = calculate_ssm_layer_positive_depths_m(1.0, layer_num, siglev_diff)  # Returns cumulative fraction to bottom of layer
        layer_bottom_depths = total_depths_m * bottom_frac  # Actual bottom depth in meters for this layer

        # Mask out cells where layer bottom exceeds species limit
        mask[0, layer_num - 1, layer_bottom_depths > species_depth_limit_m] = np.nan

    return mask


# ============================================================================
# ## Load data from *.nc file
# ============================================================================

# DEBUG/DEVELOPMENT:  HELPER CALLS TO DEFINE FOLDER AND FILE NAMES TO HARD CODE BELOW
# # #Get folder name list -do once as needed to define folders to load
# #directory_path = '../../../../SSM_output/SSM_metabolic'  #hyak and local data DO and other metabolic
# #directory_path = '/media/Data75gb_2503/SSM_outputs_kept_lg/copies_from_hyak_del/SSM_met_crab_sole_3d_copy20250910'  #crab specific--absolute path used in this cas
# directory_path = '../../../../SSM_output/SSM_data_working'
# folders = [f for f in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, f))]

# # Format the result as ['filename1', 'filename2', etc]
# formatted_folders = [f"'{folder}'" for folder in folders]
# print(f"List of all folders in \"{directory_path}\" that can be used to load files in code following:\n [{', '.join(formatted_folders)}]")
# del folders, formatted_folders, directory_path # Cleanup



import xarray as xr  # Import xarray for handling NetCDF files
import os  # Import os for directory operations

#######################Calls to load each dataset and combine in working dictionary
# Initialize empty dictionary 
SSMcalcs_dic = {}
#######################
# COMMENTED OUT - pO2 and temperature data loading (no 3D versions available)
# #Load pO2 and temperature data from SSM_saturation 
# NetCDF_input_dir = '../../../../SSM_output/SSM_saturation'  # Define the input directory of prior script outputs to load 
# subdirectories_to_load = [
#     'CalMinParam_2D_pO2_daily_min_kPa',   # Min pO2 data 
#     'CalMaxParam_2D_pO2_daily_max_kPa',   # Max pO2 data 
# ] # Specify the subdirectories to load
# loaded_datasets = load_all_nc_datasets(NetCDF_input_dir, subdirectories_to_load) # Call the function to load all NetCDF datasets from the specified subdirectories
# SSMcalcs_dic = loaded_datasets # Make dictionary using result of call to function above
# del loaded_datasets # Cleanup


####################
# # load 3D metabolic data from local Hyak copy folder
input_dir_MI_to_load = 'SSM_output/SSM_metabolic'
subdirectories_to_load = [
      f'CalMinParam_3D_{taxa}_Mindex_routine',
    # f'CalMinParam_3D_{taxa}_Mindex_basal',
    # f'CalMaxParam_3D_{taxa}_Mindex_routine',
    # f'CalMaxParam_3D_{taxa}_Mindex_basal',
    # f'CalMeanParam_3D_{taxa}_Mindex_routine',
    # f'CalMeanParam_3D_{taxa}_Mindex_basal',
    # f'CalMinParam_3D_{taxa}_Mindex_routine_ci_upper',
    # f'CalMinParam_3D_{taxa}_Mindex_basal_ci_upper',
    # f'CalMinParam_3D_{taxa}_Mindex_routine_ci_lower',
    # f'CalMaxParam_3D_{taxa}_Mindex_routine_ci_upper',
    # f'CalMaxParam_3D_{taxa}_Mindex_routine_ci_lower',
    # f'CalMaxParam_3D_{taxa}_Mindex_basal_ci_upper',
    # f'CalMaxParam_3D_{taxa}_Mindex_basal_ci_lower',
    # f'CalMinParam_3D_{taxa}_Mindex_basal_ci_lower',
    # f'CalMeanParam_3D_{taxa}_Mindex_routine_ci_upper',
    # f'CalMeanParam_3D_{taxa}_Mindex_routine_ci_lower',
    # f'CalMeanParam_3D_{taxa}_Mindex_basal_ci_upper',
    # f'CalMeanParam_3D_{taxa}_Mindex_basal_ci_lower',
]
metabolic_datasets = load_all_nc_datasets(input_dir_MI_to_load, subdirectories_to_load)#call
SSMcalcs_dic.update(metabolic_datasets) #add loaded datset
del metabolic_datasets#clean up MI
#################################
# # load 3D DO datasets  
# input_dir = '../../../../SSM_output/SSM_data_working'
# subdirectories_to_load = [
#     # 'MaxParam_WholeYear10Layers_timeseries_DOX',  # 3D DO data
#     'MinParam_WholeYear10Layers_timeseries_DOX']  # 3D DO data
# do_datasets = load_all_nc_datasets(input_dir, subdirectories_to_load)

# SSMcalcs_dic.update(do_datasets)#add loaded dataset
# del do_datasets # clean up DO

###################################

del subdirectories_to_load #final clean
print(f"All *.nc files loaded to a single working dictionary, if metabolic loaded taxa is: {taxa}") #show which taxa is loaded
print(f"Available datasets that were loaded based on subdirectories_* specified:")
for key in SSMcalcs_dic.keys():
    print(f"  - {key}")
print(f"Any specified files that can't be found will be shown as an error in above calls. Minimimal other error checking so script failure likely due to inputs and file types in the input folder not as expected.\n")

SSMcalcs_dic

