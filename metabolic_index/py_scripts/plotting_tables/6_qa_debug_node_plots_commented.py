#!/usr/bin/env python
"""
[REMOVABLE - DEBUG CODE]
Debug Node Plots
Cells 62-63 from original notebook
Contains commented debug plotting functions
"""


# ============================================================================
# ### NODE plots without export (Debug)
# ============================================================================

# # ==============================================================================
# # NODE COUNT PLOTTING - CLEAN TIME SERIES FOR ALL REGIONS AND SCENARIOS
# # ==============================================================================
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import numpy as np
# import pandas as pd

# def plot_daily_node_counts(threshold_key):
#     """
#     Create clean time series plots showing number of nodes below threshold for all regions
#     Always shows all regions, both scenarios, no statistics
    
#     Parameters:
#     threshold_key: which threshold to plot (e.g., 'threshold_2')
#     """
    
#     # Always use all regions
#     regions_to_plot = ['Hood', 'Main', 'SJF_Admiralty', 'SOG_Bellingham', 'South_Sound', 'Whidbey']
#     scenarios = ['wqm_baseline', 'wqm_reference']  #always plot both scenarios
    
#     fig, axes = plt.subplots(len(regions_to_plot), 1, figsize=(12, 2.5*len(regions_to_plot)))
#     if len(regions_to_plot) == 1:
#         axes = [axes]  #ensure axes is always a list for consistent indexing
    
#     colors = {'wqm_baseline': 'black', 'wqm_reference': 'gray'}  #scenario colors
#     labels = {'wqm_baseline': '2014 Conditions', 'wqm_reference': 'Reference'}  #scenario labels
    
#     # Get data from the boolean arrays to count nodes below threshold each day
#     daily_boolean_full = all_threshold_results[threshold_key]['ParmBelowThresh_daily_data']  #dict with (361×10×16013) boolean arrays per scenario
    
#     # Calculate y-axis limits - Hood Canal gets its own scale, others share common scale
#     max_node_counts = []  #store max node counts for non-Hood regions to determine common y-scale
#     hood_max = 0  #track Hood Canal maximum separately for its own scale
    
#     # First pass: calculate all daily node counts to determine y-axis scaling
#     for region in regions_to_plot:
#         # Get regional mask and node indices
#         region_mask = (gdf['Regions'] == region) & (gdf['included_i'] == 1)  #boolean mask for nodes in this region that are included in analysis
#         region_node_indices = np.where(region_mask)[0]  #array indices of nodes in this region
        
#         for scenario in scenarios:
#             daily_boolean_scenario = daily_boolean_full[scenario]  #(361×10×16013) boolean array for this scenario
            
#             # Calculate daily node counts for this region/scenario combination
#             daily_node_counts = []  #initialize list to store count of nodes below threshold for each of 361 days
#             for day_idx in range(361):  #loop through each day of the year
#                 day_boolean_full = daily_boolean_scenario[day_idx, :, :]  #extract boolean pattern for this day: (10×16013) depths×nodes
#                 region_boolean = day_boolean_full[:, region_node_indices]  #extract boolean for region nodes only: (10×N_region_nodes) depths×region_nodes
                
#                 # Count nodes that have any depth below threshold
#                 # region_boolean.max(axis=0) finds if any depth at each node is below threshold → (N_region_nodes,) boolean array
#                 # .sum() counts how many nodes have True (any depth below threshold) → single integer count
#                 nodes_below_threshold = region_boolean.max(axis=0).sum()  #count of nodes in this region with any depth below threshold on this day
#                 daily_node_counts.append(nodes_below_threshold)  #store daily count in list
            
#             # Track maximum for y-axis scaling
#             max_count = max(daily_node_counts)  #find maximum daily node count for this region/scenario
#             if region == 'Hood':  #Hood Canal gets separate y-axis scale due to much higher values
#                 hood_max = max(hood_max, max_count)  #track Hood Canal maximum separately
#             else:  #all other regions will share common y-axis scale
#                 max_node_counts.append(max_count)  #collect max counts for common scaling
    
#     # Set y-axis limits: Hood gets own scale, others share common scale
#     if max_node_counts:  #if there are non-Hood regions with data
#         common_ylim = max(max_node_counts) * 1.1  #add 10% buffer above maximum for other regions
#     else:  #fallback if no other regions have data
#         common_ylim = 10
    
#     hood_ylim = hood_max * 1.1  #Hood Canal y-limit with 10% buffer
    
#     # Second pass: create the actual plots
#     for i, region in enumerate(regions_to_plot):
#         ax = axes[i]  #get subplot for this region
        
#         # Get regional mask and node information
#         region_mask = (gdf['Regions'] == region) & (gdf['included_i'] == 1)  #boolean mask for nodes in this region
#         region_node_indices = np.where(region_mask)[0]  #array indices of nodes in this region
#         total_nodes_in_region = len(region_node_indices)  #count of model grid cells in this region
        
#         for scenario in scenarios:  #plot both scenarios on same subplot
#             daily_boolean_scenario = daily_boolean_full[scenario]  #(361×10×16013) boolean array for this scenario
            
#             # Calculate daily node counts for this region/scenario (same calculation as above)
#             daily_node_counts = []  #initialize list for daily node counts
#             for day_idx in range(361):  #loop through each day
#                 day_boolean_full = daily_boolean_scenario[day_idx, :, :]  #(10×16013) boolean pattern for this day
#                 region_boolean = day_boolean_full[:, region_node_indices]  #(10×N_region_nodes) extract region data
                
#                 # Count nodes below threshold (any depth at node below threshold counts the node)
#                 nodes_below_threshold = region_boolean.max(axis=0).sum()  #count nodes with any depth below threshold
#                 daily_node_counts.append(nodes_below_threshold)  #store daily count
            
#             #plot clean time series - no grid lines, no markers, no annotations
#             ax.plot(time_coords, daily_node_counts, color=colors[scenario], 
#                    linewidth=1, label=labels[scenario])  #plot time series line
        
#         #format axis - clean and simple style
#         ax.set_ylabel(f'{region}\nNodes Below Threshold\n(out of {total_nodes_in_region})', fontsize=11)  #y-label shows region name and total nodes for context
        
#         # Set y-axis scale - Hood gets its own scale due to much higher values, others share common scale
#         if region == 'Hood':
#             ax.set_ylim(0, hood_ylim)  #Hood Canal uses separate y-scale
#         else:
#             ax.set_ylim(0, common_ylim)  #other regions use common y-scale for easy comparison
        
#         # Format x-axis as days in 2014
#         ax.set_xlim(time_coords[0], time_coords[-1])  #set x-axis limits to full year
#         ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  #tick marks every 2 months
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))  #month abbreviations (Jan, Mar, May, etc.)
        
#         #add legend for first subplot only to avoid repetition
#         if i == 0:
#             ax.legend(loc='upper right', fontsize=10)  #legend showing 2014 Conditions vs Reference
    
#     #format x-axis label for bottom subplot only
#     axes[-1].set_xlabel('Days in 2014', fontsize=12)  #x-axis label only on bottom plot
    
#     #add overall title for entire figure
#     threshold_name = threshold_key.replace('threshold_', '') + ' mg/L'  #convert threshold_2 → 2 mg/L
#     plt.suptitle(f'Daily Node Count Below {threshold_name} DO Threshold', 
#                 fontsize=13, y=0.98)  #main title at top of figure
    
#     plt.tight_layout()  #adjust subplot spacing
#     plt.show()  #display the plot

# # ==============================================================================
# # USAGE EXAMPLES - NODE COUNT PLOTTING (NO STATISTICS)
# # ==============================================================================

# # Example 1: Node count plotting for threshold_2
# print("DEBUG: NODE COUNT PLOTTING (not saved to file)  FOR:")
# plot_daily_node_counts('threshold_2')

# # Example 3: Node count plotting for DO_standard
# print("Node count plotting for DO_standard may also be plotted")

