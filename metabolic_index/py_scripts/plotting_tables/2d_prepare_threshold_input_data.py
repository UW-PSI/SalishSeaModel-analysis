#!/usr/bin/env python
"""
Prepare Threshold Input Data
Cells 25 and 27 from original notebook (active code extracted from cells 22-34)
This code prepares the ssm_input_datasets needed for threshold calculations
"""

# ============================================================================
# Cell 25: Configuration and case setup
# ============================================================================

print("Noncompliance modules imported successfully")

# Print configuration info
print(f"Configuration loaded from SSM_config_{case}_working.yaml")
print(f"Shapefile path: {ssm_config['paths']['shapefile']}")
print(f"Output path: {ssm_config['paths']['processed_output']}")

# ============================================================================
# Cell 27: Prepare input datasets for threshold analysis
# ============================================================================

#SM- Simple data preparation with descriptive parameter name
# ==============================================================================
# DATA PREPARATION
# ==============================================================================

# Use pre-loaded data from existing dictionary
existing_data = SSMcalcs_dic[f'CalMinParam_3D_{taxa}_Mindex_routine'][ssm_config['run_information']['baseline']]
reference_data = SSMcalcs_dic[f'CalMinParam_3D_{taxa}_Mindex_routine'][ssm_config['run_information']['reference']]
variable_name = f'Mindex_{taxa}_routine'
excel_file_param_name = variable_name

# Extract appropriate data based on scope
if scope == 'benthic':
    # Use only bottom layer (last depth index)
    wqm_baseline_data = existing_data[variable_name].values[:, -1, :]
    wqm_reference_data = reference_data[variable_name].values[:, -1, :]
else:  # scope == 'wc'
    # Use full water column (time, depth, nodes)
    wqm_baseline_data = existing_data[variable_name].values
    wqm_reference_data = reference_data[variable_name].values

ssm_input_datasets = {
    ssm_config['run_information']['baseline']: wqm_baseline_data,
    ssm_config['run_information']['reference']: wqm_reference_data
}
print(f"Data ready - keys: {list(ssm_input_datasets.keys())}")  # [DEBUG]
