#!/usr/bin/env python3
# Created by Ben Roberts at the Puget Sound Institute with funding provided by
# King County.
#

import argparse
from pathlib import Path
import os
import logging
from datetime import date
import time

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from joblib import Parallel, delayed

from ssm_utils import read_case
from calc_below_threshold import calc_DO_below_thresh

THRESHOLDS = [1, 2, 3, 4, 5, 7, 10, 14]
LABELS = ['<1', '1-2', '2-3', '3-4', '4-5', '5-7', '7-10', '10-14']
COLORS = ['#d73027',  # <1 mg/L - dark red
          '#fc8d59',  # 1-2 mg/L - orange red  
          '#fee090',  # 2-3 mg/L - light orange
          '#ffffbf',  # 3-4 mg/L - pale yellow
          '#ffffe0',  # 4-5 mg/L - ivory/almost white (neutral, still concerning)
          '#abd9e9',  # 5-7 mg/L - light blue
          '#74add1',  # 7-10 mg/L - medium blue
          '#4575b4']  # 10-14 mg/L - dark blue

def plot_multi_threshold_stacked_volumes(case, ssm_config, run_type,
                                         show_volume_totals=False,
                                         scope=None, max_y_limit=10):
    """
    Create stacked area plots showing volume bands between DO thresholds.
    Matches existing plot style with 6 regions in vertical subplots.
    
    Parameters:
    case: SOG_nb, whidbey, etc
    ssm_config: dictionary of all case configuration
    run_type: short name of run, eg 'wqm_baseline' or 'wqm_reference'
    scope: an optional depth reduction scope, defaults to full water column
    """

    logger = logging.getLogger('plot_multi_threshold_stacked_volumes')

    # Get regional volume totals
    shp = ssm_config['paths']['shapefile']
    gdf = gpd.read_file(shp)
    regional_volumes = gdf.loc[gdf['included_i'] == 1].groupby('region_inf')['volume'].sum()

    # Compute all the daily volumes for all thresholds
    def worker(t):
        return calc_DO_below_thresh(case, ssm_config, t, shp, scope=scope, run_type=run_type)[3][run_type]
    results_raw = Parallel(n_jobs=len(os.sched_getaffinity(0)), prefer='threads')(delayed(worker)(t) for t in THRESHOLDS)
    daily_volume_results = {f'threshold_{t}': results_raw[i] for i,t in enumerate(THRESHOLDS)}

    # Load regions and time coords from first DF
    first_df = daily_volume_results[next(iter(daily_volume_results))]
    regions = first_df.columns
    time_coords = first_df.index

    # Create figure with subplots  
    fig, axes = plt.subplots(len(regions), 1, figsize=(12, 2.5*len(regions)))

    # Print total volumes if requested (following  pattern)
    if show_volume_totals:
        print(f"\\n=== Volume Statistics for {run_type} ===")
        print("Regional Total Volumes:")
        for region in regions:
            total_vol = regional_volumes.sum() if region == 'All_regions' else regional_volumes.loc[region].item()
            print(f"  {region:15}: {total_vol:6.1f} km³")

    # Track maximum y-values for consistent scaling
    max_y_values = []

    # Process each region
    for ax_idx, (ax, region) in enumerate(zip(axes, regions)):

        # Extract volumes for all thresholds
        volumes = []
        missing_thresholds = []

        for t in THRESHOLDS:
            key = f'threshold_{t}'
            volumes.append(daily_volume_results[key][region])

        # Calculate volume bands (differences between consecutive thresholds)
        bands = np.zeros((len(THRESHOLDS), len(time_coords)))
        bands[0] = volumes[0]  # Volume below 1 mg/L

        for i in range(1, len(THRESHOLDS)):
            bands[i] = volumes[i] - volumes[i-1]
            # Ensure non-negative (handle numerical issues)
            bands[i] = np.maximum(bands[i], 0)

        # Validation check and volume statistics
        total_from_bands = bands.sum(axis=0)
        total_from_last_threshold = volumes[-1]
        if not np.allclose(total_from_bands, total_from_last_threshold, rtol=1e-8):
            max_diff = np.max(np.abs(total_from_bands - total_from_last_threshold))
            logger.warning(f"Band conservation issue for {region}, max diff = {max_diff:.6f}")

        # Print daily volume statistics (following  pattern)
        if show_volume_totals:
            max_daily = np.max(total_from_bands)
            mean_daily = np.mean(total_from_bands)
            print(f"  {region:15}: Max daily = {max_daily:5.1f} km³, Mean daily = {mean_daily:5.1f} km³")

        # Create stacked area plot - FIXED: separate calls for labels
        if ax_idx == 0:
            # First subplot gets labels for legend
            stack = ax.stackplot(time_coords, bands, colors=COLORS, labels=LABELS, alpha=0.8)
        else:
            # Other subplots don't get labels parameter
            stack = ax.stackplot(time_coords, bands, colors=COLORS, alpha=0.8)

        # Formatting to match existing style
        ax.set_ylabel(f'{region}\nVolume (km³)', fontsize=11)
        ax.set_title(f'{region}', fontsize=11, fontweight='bold', loc='left')
        # Remove grid lines
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())

        # Set consistent y-axis limits for better visual comparison
        ax.set_ylim(0, max_y_limit)
        ax.set_xlim(date(time_coords.year[0], time_coords.month[0], 1), time_coords[-1].date())

        # Add total regional volume text (moved down from top)
        total_vol = regional_volumes.sum() if region == 'All_regions' else regional_volumes.loc[region].item()
        ax.text(0.02, 0.85, f'Total volume of {region}: {total_vol:.0f} km³',
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
        logger.warning(f"Some data exceeds y-limit. Consider increasing max_y_limit to {max(max_y_values)*1.1:.0f}")

    # Add legend to top subplot
    axes[0].legend(title='DO Range (mg/L)', 
                   loc='upper right', 
                   ncol=4, 
                   fontsize=9,
                   title_fontsize=10)

    # Overall title
    scenario_label = ssm_config['run_information']['run_tag'][case][run_type]
    fig.suptitle(f'Daily Volume by DO Threshold Bands - {scenario_label}', 
                fontsize=14, fontweight='bold', y=1.001)

    fig.supxlabel(f'Date ({time_coords.year[0]})', fontsize=11)
    fig.tight_layout()

    return fig

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('case', help='Case name eg SOG_nb or whidbey')
    parser.add_argument('run_type', nargs='?', help='Which run tag/scenario to plot, eg wqm_baseline. Default is all')
    parser.add_argument('--max-y-limit', '-y', type=float, default=10,
                        help='Maximum y-axis limit for better visual comparison (km³)')
    parser.add_argument('--show-volume-totals', '-t', action='store_true',
                        help='Print total volumes for each region')
    parser.add_argument('--depth', help='Optional depth reduction')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet; suppress most output')
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO)

    # Start time counter
    start = time.perf_counter()

    ssm_config, case = read_case(args.case)

    if not args.run_type:
        run_types = list(ssm_config['run_information']['run_tag'][case].keys())
    else:
        run_types = [args.run_type]

    for run_type in run_types:
        logger.info(f'Processing {run_type}')
        fig = plot_multi_threshold_stacked_volumes(case, ssm_config,
                run_type, scope=args.depth,
                max_y_limit=args.max_y_limit,
                show_volume_totals=args.show_volume_totals)

        filename = f'stacked_threshold_volumes_{run_type}{"_" + args.depth if args.depth is not None else ""}.png'
        output_path = Path(ssm_config['paths']['graphics'])
        output_path.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path / filename, dpi=150, bbox_inches='tight')
        logger.info(f"Plot saved: {output_path / filename}")

    # End time counter
    end = time.perf_counter()
    logger.info(f'Execution time: {(end - start)/60:.3f} minutes')

if __name__ == '__main__': main()
