#!/usr/bin/env python
"""
Plot Timeseries of Threshold Volumes
Cells 41-42 from original notebook
"""


# ============================================================================
# ## Timeseries plots of threshold volumes
# ============================================================================

#==============================================================================
#PLOTTING - VOLUME TIME SERIES FOR ALL REGIONS AND SCENARIOS
# ==============================================================================
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import pathlib

def plot_daily_volumes_simple(threshold_key, regions_to_plot):
    """
    Create clean time series plots showing both scenarios for all specified regions
    
    Parameters:
    threshold_key: which threshold to plot (e.g., 'threshold_2')
    regions_to_plot: list of regions to include
    """
    # Using scenarios, scenario_colors, scenario_labels initialized at beginning of script workflow

    ##regions = regions  #use regions list dynamically created in INITIALIZE AND SETUP section above
    # NOTE: To manually override region order or selection, comment out above and use eg:
    regions = ['All_regions', 'Hood', 'Main', 'SJF_Admiralty', 'SOG_Bellingham', 'South_Sound', 'Whidbey']  #match fixed_regions order for stats  # NOTE: To manually override for custom selection eg all first and no "other", toggle here no need for region = region as definedglobally earlier

    fig, axes = plt.subplots(len(regions), 1, figsize=(12, 2.5*len(regions)))
    
    all_regions_max = 0  #maximum volume for All_regions across scenarios
    hood_max = 0  #maximum volume for Hood across scenarios
    other_max = 0  #maximum volume for other regions across scenarios
    
    for region in regions:
        for scenario in scenarios:
            data = daily_volume_results[threshold_key][scenario][region]
            if region == 'All_regions':
                all_regions_max = max(all_regions_max, data.max())
            elif region == 'Hood':
                hood_max = max(hood_max, data.max())
            else:
                other_max = max(other_max, data.max())
    
    large_scale_ylim = max(all_regions_max, hood_max) * 1.1  #All_regions and Hood scale
    other_scale_ylim = other_max * 1.1  #other regions scale
    
    for i, region in enumerate(regions):
        ax = axes[i]
        
        for scenario in scenarios:  # Loops: 'wqm_baseline', then 'wqm_reference'
            #get daily volume data for this region/scenario combination
            daily_volumes = daily_volume_results[threshold_key][scenario][region]

            #plot clean time series - no grid, no markers, no annotations
            ax.plot(time_coords, daily_volumes,
                   color=scenario_colors[scenario],  # 'wqm_baseline'→'black', 'wqm_reference'→'gray'
                   linewidth=1,
                   label=scenario_labels[scenario])  # 'wqm_baseline'→'2014 Conditions', 'wqm_reference'→'Reference'
        
        #format axis - clean and simple
        ax.set_ylabel(f'{region}\nVolume (km³)', fontsize=11)
        
        if region in ['All_regions', 'Hood']:
            ax.set_ylim(0, large_scale_ylim)  #All_regions and Hood share large scale
        else:
            ax.set_ylim(0, other_scale_ylim)  #other regions share smaller scale
        
        # Format x-axis as days in 2014
        ax.set_xlim(time_coords[0], time_coords[-1])
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  #every 2 months
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))    #month abbreviations
        
        #add legend for first subplot only
        if i == 0:
            ax.legend(loc='upper right', fontsize=10)
        
        #add total regional volume text to top left corner with padding from top
        total_vol = regional_volumes.get(region, 0)  #get total volume for this region, defaults to 0 if region not found
        ax.text(0.02, 0.93, f'Total volume of {region}: {total_vol:.1f} km³', transform=ax.transAxes, 
               fontsize=9, verticalalignment='top', horizontalalignment='left')  #no background box, padded down from top
    
    #format x-axis for bottom subplot only
    axes[-1].set_xlabel('Days in 2014', fontsize=12)
    
    #add overall title with padding from top of plot box
    #threshold_name = threshold_key.replace('threshold_', '') + ' mg/L' #DO
    threshold_name = threshold_key.replace('threshold_', '')  #MI
    #plt.suptitle(f'Daily Volume Below {threshold_name} DO Threshold', # DO
    plt.suptitle(f'Daily Volume Below {threshold_name} Metabolic Index', #MI
                fontsize=13, y=0.995)  #moved down from 0.98 to 0.995 for padding from plot box
    
    plt.tight_layout()
    ### save figure to PNG file #########################################
    #save plot to PNG file BEFORE showing it
    filename = f'daily_volume_{taxa}_{threshold_key}.png'  #create filename matching threshold name
    filepath = pathlib.Path(output_plots_dir) / filename  #use plot directory from initialization
    plt.savefig(filepath, dpi=300, bbox_inches='tight')  #save as high-resolution PNG with tight bounding box
    print(f"[DEBUG] Saved plot to: {filepath}")  #show save location    
    #plt.show()  #display plot after saving [debug]

###############CALL PLOTTING FUNCTION FOR ALL THRESHOLDS ################
# Loop through all thresholds for plotting
for threshold_key in daily_volume_results.keys():  #loop through all available thresholds
    print(f"=== PLOTTING {threshold_key.upper()} ===")
    plot_daily_volumes_simple(threshold_key, [])  #regions_to_plot parameter ignored since function uses fixed_regions list

# # Call plotting function specific for just one
# print("=== PLOTTING THRESHOLD 2 ===")
# plot_daily_volumes_simple('threshold_2', [])  #regions_to_plot parameter ignored since function uses fixed_regions list

