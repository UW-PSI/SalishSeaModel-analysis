#!/usr/bin/env python
"""
Apply Habitat and Depth Masks
Cells 12-14 from original notebook
"""


# ============================================================================
# ## Habitat and depth down-selection masking- NaN applied to all nodes to exclude from further calcs/plots etc
# ============================================================================

# ==============================================================================
# Load Shapefile and Calculate volume2D (Full Water Column)
# ==============================================================================
# ensure gdf exists before habitat mask creation so that it can be called
# Note: ssm_config already loaded in 1_initialize_load_netcdf_config.py

# ==============================================================================

gdf = clean_shapefile_check16012_len(ssm_config['paths']['shapefile']) #call function tloads from this path then checks for shape with 16013 nodes and removes error row to make it 16012
print(f"\n[DEBUG] Load and clean shapefile:")
gdf = gdf.rename(columns={'region_inf': 'Regions'})  #rename region column to 'Regions' for consistency with analysis code
print(f"[DEBUG] complet \n")
regions = gdf[['node_id', 'Regions']].groupby('Regions').count().index.to_list()  #extract list of unique region names from shapefile by grouping nodes
regions.remove('Other')  #exclude 'Other' region from analysis (boundary/undefined nodes)
regions.append('All_regions')  #add 'All_regions' as virtual region representing all included nodes across entire domain (not in shapefile, calculated dynamically)

nnodes = len(gdf)  #count total number of nodes in shapefile for array sizing
nlevels = 10  #number of vertical depth layers in SSM model (fixed structure)
volume = np.asarray(gdf.volume)  #extract base volume per node (km³) from shapefile volume column as numpy array
depth_fraction = np.array(ssm_config['siglev_diff']) / 100  #convert layer depth percentages [3.2, 5.7, ..., 14.6] to fractions [0.032, 0.057, ..., 0.146] for volume distribution
volume2D = np.dot(volume.reshape(nnodes, 1), depth_fraction.reshape(1, nlevels))  #matrix multiply (N_nodes×1) × (1×10) to create (N_nodes×10) volume array distributing each node's volume across 10 layers

print(f"[DEBUG] Calculated volume2D from shapefile: {volume2D.shape}")  #confirm array dimensions (should be N_nodes×10)
print(f"[DEBUG] Regions extracted from shapefile: {regions}")  #show region list for verification

######################################################################################
# HABITAT SELECTION MASK: Apply fuction to depth and spatial filtering for all datasets
######################################################################################
# === Initialize using depth limit from 1_initialize_load_netcdf_config.py ===
habitat_depth_mask = create_species_habitat_mask_standard_grid_structure(gdf, species_depth_limit_m)  # Uses species_depth_limit_m from 1_initialize

# === DEPTH LAYER FILTERING (controlled by layer_filter_mode from 1_initialize_load_netcdf_config.py) ===
# To change mode, edit layer_filter_mode in 1_initialize_load_netcdf_config.py
if layer_filter_mode == 'bottom_only':
    habitat_depth_mask[0, 0:9, :] = np.nan  #keep bottom layer only (NaN layers 0-8, keep layer 9) - benthic species
elif layer_filter_mode == 'surface_only':
    habitat_depth_mask[0, 1:10, :] = np.nan  #surface layer only (NaN layers 1-9, keep layer 0)
elif layer_filter_mode == 'top_3':
    habitat_depth_mask[0, 3:10, :] = np.nan  #top 3 layers only (NaN layers 3-9, keep layers 0-2)
elif layer_filter_mode == 'all_layers':
    pass  # No masking - keep all 10 layers for full water column analysis
else:
    print(f"WARNING: Unknown layer_filter_mode '{layer_filter_mode}'. Using all layers.")

#
# === FURTHER SPATIAL FILTERING ( not applied but can b sequentially to refine mask) ===  - CURRENTLY NOT FULLY ADAPTED -GET WORKING THEN APLY WITH A DEPTH FUNCTION
# # Example: Keep only Hood Canal nodes, NaN all others
# hood_mask = (gdf['Regions'] == 'Hood') & (gdf['included_i'] == 1)  #boolean mask for Hood nodes
# non_hood_indices = np.where(~hood_mask)[0]  #indices of all non-Hood nodes
# habitat_depth_mask[0, :, non_hood_indices] = np.nan  #NaN all depths for non-Hood nodes

# # Example: Exclude nodes not in included_i (apply to all regions)
# excluded_mask = (gdf['included_i'] == 0)  #boolean mask for excluded nodes (land, boundary, etc.)
# excluded_indices = np.where(excluded_mask)[0]  #indices of excluded nodes
# habitat_depth_mask[0, :, excluded_indices] = np.nan  #NaN all depths for excluded nodes (ensures only water nodes remain)

# === DEPTH FILTERING DEBUG ===
kept_layers = [i for i in range(10) if not np.isnan(habitat_depth_mask[0, i, 0])]  # which layers kept
total_non_nan_nodes = np.sum(np.any(~np.isnan(habitat_depth_mask[0, :, :]), axis=0))  # nodes with at least one non-NaN layer
print(f"[DEBUG] Habitat mask applied (depth<{species_depth_limit_m}m, then layer filtering):")
print(f"[DEBUG]   Layers retained: {kept_layers} (after NaN applied to unwanted layers)")
print(f"[DEBUG]   Nodes with valid data: {total_non_nan_nodes:,} (some may be zeroed by layer mask)")
# for layer in kept_layers:  # show node count per kept layer
#     nodes_in_layer = np.sum(~np.isnan(habitat_depth_mask[0, layer, :]))
#     print(f"[DEBUG]     Layer {layer}: {nodes_in_layer:,} nodes")


# === DEBUG -APPLY HABITAT MASK: Iterate over each dictionary in SSMcalcs_dic and apply NaN mask to all data variables ===
count_displayed_with_NaNs = 1  # Set to 'ALL' for all variables, or number (0, 1, 2, 3...) for limited examples (0 = silent)

debug_counter = 0  # Counter to track how many debug outputs we've shown so far
for dataset_key in SSMcalcs_dic.keys():
    for scenario_key in SSMcalcs_dic[dataset_key].keys():
        for var_name in SSMcalcs_dic[dataset_key][scenario_key].data_vars:
            # Check if we should show debug for this variable
            show_debug = (count_displayed_with_NaNs == 'ALL' or debug_counter < count_displayed_with_NaNs)
            
            if show_debug:
                before = np.isnan(SSMcalcs_dic[dataset_key][scenario_key][var_name].values).sum()
                print(f"[DEBUG] Before - {dataset_key}/{scenario_key}/{var_name}: {before:,} NaNs")
            
            SSMcalcs_dic[dataset_key][scenario_key][var_name].values *= habitat_depth_mask  #apply mask via multiplication
            
            if show_debug:
                after = np.isnan(SSMcalcs_dic[dataset_key][scenario_key][var_name].values).sum()
                print(f"[DEBUG] After  - {dataset_key}/{scenario_key}/{var_name}: {after:,} NaNs (+{after-before:,})")
                debug_counter += 1
print("[DEBUG] Habitat mask applied to all datasets\n")


