#!/usr/bin/env python
"""
Plot Stacked Volumes - Working and Commented Versions
Cells 51-57 from original notebook
Contains both working implementation and commented non-working attempt
"""


# ============================================================================
# ## Timeseries plot Multi-threshold stacked volume
# ============================================================================

# Multi-Threshold Stacked Volume Analysis
#**Purpose:** Create stacked area plots showing daily volume bands between DO thresholds.
#**Implementation:** Uses existing `daily_volume_results` data structure to create visualization showing volume in each DO range (e.g., <1, 1-2, 2-3, etc. mg/L).
#**Output:** Stacked area plots with 6 regions (matching existing style) and pastel oceanographic color scheme.

# ==============================================================================
# MULTI-THRESHOLD STACKED VOLUME ANALYSIS - Daily volume bands between DO thresholds  ONLY - does not porduce MI
# ==============================================================================

# CONFIGURABLE PARAMETERS - Adjust and re-run this cell
max_y_limit = 10  # Maximum y-axis limit for better visual comparison (km³)
show_volume_totals = True  # Print total volumes for each region

def plot_multi_threshold_stacked_volumes(scenario='wqm_baseline', save_plot=True):
    """
    Create stacked area plots showing volume bands between DO thresholds.
    Matches existing plot style with 6 regions in vertical subplots.
    
    Parameters:
    scenario: 'wqm_baseline' or 'wqm_reference'  
    save_plot: whether to save figure to output directory
    """
    
    # Configuration of plots: 
    thresholds = [1, 2, 3, 4, 5, 7, 10, 14]  # Exclude 6 for cleaner bands
    ## regions = regions  #use regions list from daily volume section (line with gdf shapefile extraction) no ned to redefine here as globally defined earlier 
    regions = ['All_regions','Hood', 'Main', 'SJF_Admiralty', 'SOG_Bellingham', 'South_Sound', 'Whidbey']  #manual override without all and other     # NOTE: To manually override for custom selection eg all first and no "other", toggle here no need for region = region as definedglobally earlier 
    # Regional total volumes (following # pattern) #Defined earlier with volume initialization
    # regional_volumes = regional_volumes
 
    # Color scheme: Red (hypoxic) to Blue (good) - pastel oceanographic
    colors = ['#d73027',  # <1 mg/L - dark red
              '#fc8d59',  # 1-2 mg/L - orange red  
              '#fee090',  # 2-3 mg/L - light orange
              '#ffffbf',  # 3-4 mg/L - pale yellow
              '#ffffe0',  # 4-5 mg/L - ivory/almost white (neutral, still concerning)
              '#abd9e9',  # 5-7 mg/L - light blue
              '#74add1',  # 7-10 mg/L - medium blue
              '#4575b4']  # 10-14 mg/L - dark blue
    
    labels = ['<1', '1-2', '2-3', '3-4', '4-5', '5-7', '7-10', '10-14']
    

    
    # Create figure with subplots  
    fig, axes = plt.subplots(len(regions), 1, figsize=(12, 2.5*len(regions)))
    
    # Print total volumes if requested (following  pattern)
    if show_volume_totals:
        print(f"\\n=== Volume Statistics for {scenario.upper()} ===")
        print("Regional Total Volumes:")
        for region in regions:
            total_vol = regional_volumes.get(region, 0)
            print(f"  {region:15}: {total_vol:6.1f} km³")
    
    # Track maximum y-values for consistent scaling
    max_y_values = []
    
    # Process each region
    for ax_idx, (ax, region) in enumerate(zip(axes, regions)):
        
        # Extract volumes for all thresholds
        volumes = []
        missing_thresholds = []
        
        for t in thresholds:
            key = f'threshold_{t}'
            if key in daily_volume_results and scenario in daily_volume_results[key]:
                if region in daily_volume_results[key][scenario]:
                    volumes.append(daily_volume_results[key][scenario][region])
                else:
                    print(f"Warning: region {region} not found for {key}")
                    missing_thresholds.append(t)
            else:
                print(f"Warning: {key} not found in daily_volume_results")
                missing_thresholds.append(t)
        
        if missing_thresholds:
            print(f"Skipping thresholds {missing_thresholds} for {region}")
            continue
            
        if len(volumes) != len(thresholds):
            print(f"Warning: Only found {len(volumes)}/{len(thresholds)} thresholds for {region}")
            continue
        
        # Calculate volume bands (differences between consecutive thresholds)
        bands = np.zeros((len(thresholds), len(time_coords)))
        bands[0] = volumes[0]  # Volume below 1 mg/L
        
        for i in range(1, len(thresholds)):
            bands[i] = volumes[i] - volumes[i-1] 
            # Ensure non-negative (handle numerical issues)
            bands[i] = np.maximum(bands[i], 0)
        
        # Validation check and volume statistics
        total_from_bands = bands.sum(axis=0)
        total_from_last_threshold = volumes[-1]
        if not np.allclose(total_from_bands, total_from_last_threshold, rtol=1e-8):
            max_diff = np.max(np.abs(total_from_bands - total_from_last_threshold))
            print(f"Warning: Band conservation issue for {region}, max diff = {max_diff:.6f}")
        
        # Print daily volume statistics (following  pattern)
        if show_volume_totals:
            max_daily = np.max(total_from_bands)
            mean_daily = np.mean(total_from_bands)
            print(f"  {region:15}: Max daily = {max_daily:5.1f} km³, Mean daily = {mean_daily:5.1f} km³")
        
        # Create stacked area plot - FIXED: separate calls for labels
        if ax_idx == 0:
            # First subplot gets labels for legend
            stack = ax.stackplot(time_coords, bands, colors=colors, labels=labels, alpha=0.8)
        else:
            # Other subplots don't get labels parameter
            stack = ax.stackplot(time_coords, bands, colors=colors, alpha=0.8)
        
        # Formatting to match existing style
        ax.set_ylabel(f'{region}\nVolume (km³)', fontsize=11)
        ax.set_title(f'{region}', fontsize=11, fontweight='bold', loc='left')
        # Remove grid lines
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        
        # Set consistent y-axis limits for better visual comparison
        ax.set_ylim(0, max_y_limit)
        
        # Add total regional volume text (moved down from top)
        total_vol = regional_volumes.get(region, 0)
        ax.text(0.02, 0.85, f'Total volume of {region}: {total_vol:.1f} km³', 
                transform=ax.transAxes, fontsize=9, 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Store max y-value for reference
        current_max = np.max(total_from_bands)
        max_y_values.append(current_max)
    
    # Print overall statistics
    if show_volume_totals:
        print(f"\\nUsing y-axis limit: {max_y_limit} km³ (configurable at top of cell)")
        print(f"Actual max volumes: {max(max_y_values):.1f} km³")
        if max(max_y_values) > max_y_limit:
            print(f"⚠️  Some data exceeds y-limit. Consider increasing max_y_limit to {max(max_y_values)*1.1:.0f}")
    
    # Add legend to top subplot
    #axes[0].legend(title='DO Range (mg/L)', #DO
    axes[0].legend(title='Metabolic Index (Unitless)', #MI
                   loc='upper right', 
                   ncol=4, 
                   fontsize=9,
                   title_fontsize=10)
    
    # Overall title
    scenario_label = '2014 Conditions' if scenario == 'wqm_baseline' else 'Reference'
    plt.suptitle(f'Daily Volume by Threshold Bands - {scenario_label}', 
                fontsize=14, fontweight='bold', y=1.001)
    
    plt.xlabel('Date (2014)', fontsize=11)
    plt.tight_layout()
    
    # Save and show plot 
    if save_plot:#safe first
        output_path = pathlib.Path(output_plots_dir)  #use plot directory from initialization where it is created if it does not exist
        filename = f'multi_threshold_stacked_volumes_{scenario}.png'
        plt.savefig(output_path / filename, dpi=150, bbox_inches='tight')
        print(f"Plot saved: {output_path / filename}")
    plt.show() #show after 

##################### CALL THE FUNCTION TO CREATE PLOTS -SKIP  IF NOT Dissolved Oxygen with all thresholds needed ##################### 
# Call the function for baseline  and reference scenarios for DO ONLY
# Check if stacked plot thresholds available, otherwise save explanation to file
required_for_stacked = [1, 2, 3, 4, 5, 7, 10, 14] #thresholds needed for DO stacked plot
missing = [t for t in required_for_stacked if f'threshold_{t}' not in daily_volume_results] #check what's missing from current run

if missing: #if any required thresholds are missing
    print(f"[DEBUG] Skipping stacked plots - missing thresholds: {missing}. See output file for details.") #notify user # added stacked plot skip notification
    with open(pathlib.Path(output_plots_dir) / 'Multi_threshold_stacked_volumes_png_missing_thresholds_Outputs_for_DO_not_Metabolic_Index.txt', 'w') as f: f.write(f"Stacked plot requires thresholds: {required_for_stacked}\nMissing: {missing}\nAvailable: {[k.replace('threshold_', '') for k in daily_volume_results.keys() if k.startswith('threshold_')]}\nNote: Stacked plot is for full DO water column analysis\nTo generate, run with: thresholds_to_run = {required_for_stacked}") #save explanation to file # write missing threshold details to text file in plot directory
else: #if all required thresholds are present
    print("=== Creating Multi-Threshold Stacked Volume Plot (for DO outputs not Metabolic Index) ===") #status message
    plot_multi_threshold_stacked_volumes('wqm_baseline', save_plot=True) #create baseline stacked plot
    print("\\n=== Creating Reference Scenario Plot ===") #status message
    plot_multi_threshold_stacked_volumes('wqm_reference', save_plot=True) #create reference stacked plot

