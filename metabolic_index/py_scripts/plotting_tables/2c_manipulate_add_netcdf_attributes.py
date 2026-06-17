#!/usr/bin/env python
"""
Add NetCDF Attributes to Datasets
Cells 17-21 from original notebook
"""


# ============================================================================
# ## In Xarray directly assign attributes where missing
# ============================================================================

## add Add descriptive attributes to NetCDF files in a dictionary but working at the root name level eg MinParm

def add_parameters_to_netcdf_files_in_dictionary(data_dict, datasets, param_types, parameters):
    """
    Add descriptive attributes to NetCDF files in a dictionary.

    Parameters:
    data_dict (dict): The dictionary containing the NetCDF files.
    datasets (list): List of dataset names.
    param_types (list): List of parameter types.
    parameters (dict): Dictionary of parameters and their attributes.
    """
    # Loop through each parameter type, parameter, dataset, and data array
    print(f'Starting parameter update of all datarrays and datasets in specified dictionary')
    for param_type in param_types:
        for param, attrs in parameters.items():
            for dataset in datasets:
                key = f'{param_type}_timeseries_{param}'
                if key in data_dict:
                    if dataset in data_dict[key]:
                        print(f'Checking: {key} -> {dataset}:')  # Debug statement
                        for data_array in data_dict[key][dataset]:
                            # Assign descriptive attributes to the DataArray
                            data_dict[key][dataset][data_array].attrs['long_name'] = attrs['long_name']
                            data_dict[key][dataset][data_array].attrs['units'] = attrs['units']
                            print(f'Long name and units added for {key} -> {dataset} -> {data_array}')  # Debug statement
                    else:
                        print(f'***Error: Dataset "{dataset}" not found in {key}, skipping and moving to next- this will only change the names shown in plots etc not function calls')  # Error message
                else:
                    print(f'***Warning: Key "{key}" not found in top-level dictionary, skipping and moving to next -this will only change the names shown in plots etc not function calls')  # Warning message
    print(f'Completed of all datarrays and datasets in specified dictionary')
# Shared inputs:
datasets = ['exist', 'wqm_reference']
param_types = ['MinParam', 'MeanParam', 'MaxParam']
parameters = {
    'DOX': {'long_name': 'Dissolved Oxygen', 'units': 'mg/L'},
    'temp': {'long_name': 'Temperature', 'units': '°C'},
    'sal': {'long_name': 'Salinity', 'units': 'PPT'},
    'NO3': {'long_name': 'NO3', 'units': 'N mg/L'},
    'NH4': {'long_name': 'NH4', 'units': 'N mg/L'},
    'B1': {'long_name': 'Phytoplankton B1', 'units': 'g/m3'},
    'B2': {'long_name': 'Phytoplankton B2', 'units': 'g/m3'}
}
#call:
add_parameters_to_netcdf_files_in_dictionary(SSMcalcs_dic, datasets, param_types, parameters)

def add_parameters_directly_to_netcdf_files_in_dictionary(data_dict, datasets, specific_parameters):
    """
    Add descriptive attributes directly to NetCDF files in a dictionary.

    Parameters:
    data_dict (dict): The dictionary containing the NetCDF files.
    datasets (list): List of dataset names.
    specific_parameters (dict): Dictionary of specific parameters and their attributes.
    """
    # Loop through each parameter, dataset, and data array
    for param, attrs in specific_parameters.items():
        for dataset in datasets:
            if param in data_dict:
                if dataset in data_dict[param]:
                    print(f'Checking: {param} -> {dataset}:')  # Debug statement
                    for data_array in data_dict[param][dataset].data_vars:
                        # Assign descriptive attributes to the DataArray
                        data_dict[param][dataset][data_array].attrs['long_name'] = attrs['long_name']
                        data_dict[param][dataset][data_array].attrs['units'] = attrs.get('units', '')
                        print(f'Long name and units added for {param} -> {dataset} -> {data_array}')  # Debug statement
                else:
                    print(f'***Error: Dataset "{dataset}" not found in {param}, skipping and moving to next -this will only change the names shown in plots etc not function calls')  # Error message
            else:
                print(f'***Warning: Key "{param}" not found in top-level dictionary, skipping and moving to next -this will only change the names shown in plots etc not function calls')  # Warning message

# Specific naming to add for each dataset

datasets = ['exist', 'wqm_reference']
specific_parameters = {
    # === DO DATASET VARIABLES ===
    'MinParam_timeseries_DOX': {'long_name': 'Dissolved Oxygen (Min Daily)', 'units': 'mg/L'},
    'MaxParam_timeseries_DOX': {'long_name': 'Dissolved Oxygen (Max Daily)', 'units': 'mg/L'},

    # === pO2 DATASET VARIABLES ===
    'CalMinParam_2D_pO2_daily_min_kPa': {'long_name': 'Partial Pressure Of Oxygen (Min Daily)', 'units': 'kPa'},
    'CalMaxParam_2D_pO2_daily_max_kPa': {'long_name': 'Partial Pressure Of Oxygen (Max Daily)', 'units': 'kPa'},

    # === temp DATASET VARIABLES ===
    'CalMinParam_2D_temp_daily_mean_CT': {'long_name': 'Temperature (Min Daily Mean)', 'units': '°C'},
    'CalMaxParam_2D_temp_daily_mean_CT': {'long_name': 'Temperature (Max Daily Mean)', 'units': '°C'},

    # === METABOLIC INDEX VARIABLES ===
    f'CalMinParam_2D_{taxa}_Mindex_routine': {'long_name': f'{taxa.title()} Metabolic Index Routine (Min Daily)'},
    f'CalMaxParam_2D_{taxa}_Mindex_routine': {'long_name': f'{taxa.title()} Metabolic Index Routine (Max Daily)'},
    f'CalMinParam_2D_{taxa}_Mindex_basal': {'long_name': f'{taxa.title()} Metabolic Index Basal (Min Daily)'},
    f'CalMaxParam_2D_{taxa}_Mindex_basal': {'long_name': f'{taxa.title()} Metabolic Index Basal (Max Daily)'},
    f'CalMinParam_2D_{taxa}_Mindex_routine_ci_upper': {'long_name': f'{taxa.title()} Metabolic Index Routine p95 (Min Daily)'},
    f'CalMaxParam_2D_{taxa}_Mindex_routine_ci_upper': {'long_name': f'{taxa.title()} Metabolic Index Routine p95 (Max Daily)'},
    f'CalMinParam_2D_{taxa}_Mindex_routine_ci_lower': {'long_name': f'{taxa.title()} Metabolic Index Routine p05 (Min Daily)'},
    f'CalMaxParam_2D_{taxa}_Mindex_routine_ci_lower': {'long_name': f'{taxa.title()} Metabolic Index Routine p05 (Max Daily)'},
    f'CalMinParam_2D_{taxa}_Mindex_basal_ci_upper': {'long_name': f'{taxa.title()} Metabolic Index Basal p95 (Min Daily)'},
    f'CalMaxParam_2D_{taxa}_Mindex_basal_ci_upper': {'long_name': f'{taxa.title()} Metabolic Index Basal p95 (Max Daily)'},
    f'CalMinParam_2D_{taxa}_Mindex_basal_ci_lower': {'long_name': f'{taxa.title()} Metabolic Index Basal p05 (Min Daily)'},
    f'CalMaxParam_2D_{taxa}_Mindex_basal_ci_lower': {'long_name': f'{taxa.title()} Metabolic Index Basal p05 (Max Daily)'}
}

add_parameters_directly_to_netcdf_files_in_dictionary(SSMcalcs_dic, datasets, specific_parameters)
del datasets, specific_parameters # cleanup after function


# ============================================================================
# ## Add existing -reference for each dataarray (not done currently)
# ============================================================================

# def add_dataarray_existing_minus_ref(data_dict):
#     """
#     Add a new dataset 'existing_minus_ref' by subtracting 'wqm_reference' from 'exist'.

#     Parameters:
#     data_dict (dict): The dictionary containing the NetCDF files.
#     """
#     # Iterate through the keys of the data_dict
#     for key in data_dict:
#         if 'exist' in data_dict[key] and 'wqm_reference' in data_dict[key]:
#             # Create a true copy of 'exist' dataset
#             data_dict[key]['existing_minus_ref'] = data_dict[key]['exist'].copy(deep=True)
#             print(f"Created a true copy of 'exist' for key: {key}")

#             # Subtract the entire dataset 'wqm_reference' from 'exist'
#             data_dict[key]['existing_minus_ref'] = data_dict[key]['exist'] - data_dict[key]['wqm_reference']
#             print(f"Subtracted 'wqm_reference' from 'exist' for key: {key}")
#         else:
#             print(f"'exist' or 'wqm_reference' not found for key: {key}, skipping")

#     print("Subtraction of data arrays complete.")



# add_dataarray_existing_minus_ref(SSMcalcs_dic)

