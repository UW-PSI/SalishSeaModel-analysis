#!/usr/bin/env python3
"""
Super-Simplified Modular Analysis Runner
========================================
Created: 2026-06-17
Purpose: Generic template for running modular Python analysis pipelines

USAGE:
------
python plotting_tables.py    # Runs with automatic logging

To skip a module: Comment out its line in the list below
"""

from pathlib import Path
import argparse

from helper_ExportsAndFigs import *
import helper_variable_name_datasetreview
from helper_create_statistics_dataframes import create_statistics_dataframes
from ssm_utils import read_case


def main():
    global case, ssm_config
    parser = argparse.ArgumentParser()
    parser.add_argument('case')
    parser.add_argument('species')
    args = parser.parse_args()
    modpath = Path(__file__).parent / 'plotting_tables'

    ssm_config, case = read_case(args.case)

    # Initialize and load NetCDF data - Species specific
    if args.species == 'crab':
        exec(open(modpath / '1a_routine_crab_80m_habitat_initialize_load_netcdf_config.py').read(), globals())
    elif args.species == 'salmon':
        exec(open(modpath / '1b_routine_salmon_100m_habitat_initialize_load_netcdf_config.py').read(), globals())
    elif args.species == 'sole':
        exec(open(modpath / '1c_routine_sole_100m_habitat_initialize_load_netcdf_config.py').read(), globals())
    # Apply habitat & depth masks
    exec(open(modpath / '2a_manipulate_habitat_depth_masks.py').read(), globals())
    # Calculate total volumes by region
    exec(open(modpath / '2b_manipulate_calculate_regional_volumes.py').read(), globals())
    # Add NetCDF attributes
    exec(open(modpath / '2c_manipulate_add_netcdf_attributes.py').read(), globals())
    # Prepare ssm_input_datasets
    exec(open(modpath / '2d_prepare_threshold_input_data.py').read(), globals())
    # Threshold calculations & export to an Excel file
    exec(open(modpath / '3a_calculate_thresholds_with_excel.py').read(), globals())
    # Timeseries plotting
    exec(open(modpath / '3b_plot_timeseries_threshold_volumes.py').read(), globals())
    # All stacked plots versions
    exec(open(modpath / '3c_plot_stacked_volumes_working_and_commented.py').read(), globals())
    # Create volume stats DFs & add to existing Excel files
    exec(open(modpath / '4a_create_volume_statistics_dataframes.py').read(), globals())
    # Create pivot summary in additional Excel file
    exec(open(modpath / '4b_create_pivot_summary_dataframes.py').read(), globals())
    # Create area/node DFs & add to the existing Excel files
    exec(open(modpath / '4c_create_area_node_statistics_dataframes_excel.py').read(), globals())

if __name__ == '__main__': main()
