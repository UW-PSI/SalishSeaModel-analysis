#!/usr/bin/env python3
# %% [markdown]
# # Saturation (pO2 for metabolic calcualations)

# %%
# 2025.01.09 Mazzilli  -updating to v3 of saturation scripts using vary do and average temp/sal inputs

# Saturation and AOU calculations that are then used for Metabolic scripts following
# 
# This script calculates partial pressure of oxygen (pO₂) for three DO scenarios:
#   - Minimum pO₂: using min DO + mean salinity + mean temperature
#   - Maximum pO₂: using max DO + mean salinity + mean temperature  
#   - Mean pO₂: using mean DO + mean salinity + mean temperature
# Using mean temperature and mean salinity avoids unrealistic combinations (e.g., min pO₂ rarely co-occurs with min temperature).

# All three blocks are ACTIVE and run sequentially to produce outputs for metabolic index calculations.
## note that blocks can work independently calling min or max DO  saturation function and export blocks wi the other  commented out if there are issues with memory 

# %% [markdown]
# # Workflow Description

# %% [markdown]
# **Purpose:**  
# - Compute DO saturation (mg/L and %), partial pressure of oxygen (pO₂, kPa), and AOU (mg/L) for each grid cell, depth, and time step in the SSM output.
# - Prepare and export these results as NetCDF and Excel files for further metabolic and QA analyses.
# 
# ---
# 
# ***Key Steps***
# 
# **1. Data Loading:**  
# - Loads NetCDF datasets from SSM output subdirectories using `load_all_nc_datasets`.  
#   Example: `/SSM_data_working/MinParam_WholeYear10Layers_timeseries_DOX/exist.nc`, DataArray: `DOXG_daily_min_wc`
# 
# **2. Depth & Pressure Calculation:**  
# - Calculates mid-layer depths for each SSM grid cell with `calculate_mid_layer_depth_from_surface`.  
# - Broadcasts depth, latitude, longitude, and sea pressure to 3D arrays.  
# - **All calculations use the GSW (Gibbs SeaWater) toolbox from UNESCO (TEOS-10 standard).**
# 
# **3. Saturation & AOU Calculation:**  
# - Uses `calculate_saturation_and_aou` to compute:  
#   - **DO saturation (mg/L):** `solubility_GSW_output = gsw.O2sol(SA, CT, P)`  
#   - **DO percent saturation (%):** `DO_percent_saturation = (DO_measured / DO_saturation) * 100`
#   - **Partial pressure of oxygen (pO₂, kPa):** `pO2_insitu_kPa = (DO_measured / DO_saturation) * (P_atm * 0.2095)`
#     where `P_total = 101.3253 + (sea_pressure_dbar × 10.0 × (density/1025))`
#     (101.3253 = atmospheric pressure at sea level (kPa), 10.0 = dbar to kPa exact conversion, 0.2095 = O₂ mole fraction, density = in-situ seawater density)
#   - **AOU (mg/L):** `DO_AOE_mg_l = DO_saturation - DO_measured`  
# - *See the detailed function description and references in the markup section below for further explanation of calculation methods and scientific background.*
# 
# **4. Result Storage:**  
# - Stores results in a nested dictionary structure, matching the SSM model run keys.  
#   Example structure: `SSMcalcs_dic['CalMinParam_3D_DO_percent_saturation']['exist']['DO_percent_saturation']`
# 
# **5. Export:**  
# - Exports 3D and 2D (depth-averaged/layer-selected) results as NetCDF files using `export_dictionary_of_nc_datasets`.
# - Filters results for specific nodes with `filter_by_specific_nodes` and exports as Excel files using `export_xarray_dict_to_excel`.
# 
# ---
# 
# ***Input/Output Directories and File Naming***
# 
# **Input Example:**  
# - `/SSM_data_working/MinParam_WholeYear10Layers_timeseries_DOX/exist.nc`, DataArray: `DOXG_daily_min_wc`
# 
# **Output Examples:**  
# - NetCDF: `/SSM_output/SSM_saturation/CalMinParam_3D_DO_percent_saturation/exist.nc`
# - Excel: `/SSM_output/Excel_export_specific_node/CalMinParam_2D_DO_percent_saturation_SpecificNodes/exist.xlsx`

# %% [markdown]
# # Calculation of pO2, saturation, and AOU - description and references

# %% [markdown]
# The Salish Sea model provides DO and Salinity concentration (mg/L) and temperature in (°C). Here we calculate:
# 
# **DO Saturation (mg/L and %)** – The theoretical maximum oxygen solubility in water at a given temperature, salinity, and pressure. The calculation of solubility uses the Garcia & Gordon (1992)<sup>2</sup> equation, based on Benson & Krause (1984)<sup>1</sup>, implemented in the Gibbs SeaWater (GSW) Oceanographic Toolbox<sup>3</sup> and described in McDougall and Barker, (2011)<sup>4</sup>.
# 
# **DO Partial Pressure (pO₂, kPa)** – The pressure exerted by oxygen in the dissolved phase, proportional to its concentration and the total pressure.
# 
# **Apparent Oxygen Utilization (AOU, mg/L)** – is an estimate of the O₂ utilization due to biochemical processes and is calculated as the difference between this saturation value and measured DO. AOU (and percent saturation) were applied following NOAA (2013)<sup>5</sup>, extending surface application to all depths of the SSM, and accounting for differences in hydrostatic pressure using the GSW toolbox.
#   
# **References:**
# 
# 1.  Benson, B. B., & Krause, D. (1984). The concentration and isotopic fractionation of oxygen dissolved in freshwater and seawater in equilibrium with the atmosphere<sup>1</sup>. *Limnology and Oceanography*, *29*(3), 620–632. https://doi.org/10.4319/lo.1984.29.3.0620
# 2.  Garcia, H. E., & Gordon, L. I. (1992). Oxygen solubility in seawater: Better fitting equations. *Limnology and Oceanography*, *37*(6), 1307–1312. https://doi.org/10.4319/lo.1992.37.6.1307
# 3.  Python code libraries developed made available by the International Thermodynamic Equation of Seawater -2010 (TEOS-10) working group, adopted by the Intergovernmental Oceanographic Commission of UNESCO. Version 3.05 was downloaded from https://www.teos-10.org/pubs/gsw/html/, January 9, 2025.
# 4.  McDougall, T. J., & Barker, P. M. (2011). Getting started with TEOS-10 and the Gibbs Seawater (GSW) oceanographic toolbox. *Scor/Iapso WG*, *127*(532), 1–28.
# 5. NOAA. (2013). NOAA Atlas NESDIS 75 World Ocean Atlas 2013 Volume 3: Dissolved Oxygen, Apparent Oxygen Utilization, and Oxygen Saturation. NOAA, Silver Spring, MD. https://www.researchgate.net/publication/285117043_Dissolved_Oxygen_Apparent_Oxygen_Utilization_and_Oxygen_Saturation
# 
#   
# 
# ---
# ---  
# **Further details on application:**
# 
# Calculates dissolved oxygen metrics from oceanographic data:
# 
# - **DO Saturation (mg/L and %)** – Maximum oxygen solubility at given T, S, P
# - **DO Partial Pressure (pO₂, kPa)** – Pressure exerted by dissolved oxygen
# - **Apparent Oxygen Utilization (AOU, mg/L)** – Estimate of O₂ consumption
# 
# **Inputs required** (as arrays, all same length):
# - Dissolved oxygen concentration (mg/L)
# - Salinity (ppt)
# - Temperature (°C)
# - Depth (m, NOTE must be negative values for GSW toolbox)
# - Latitude (decimal degrees)
# - Longitude (decimal degrees)
# 
# **Core calculation method**: Uses GSW (Gibbs SeaWater) Oceanographic Toolbox (TEOS-10 framework) with O₂ solubility based on Garcia & Gordon (1992), converted through Absolute Salinity and Conservative Temperature.
# 
# ---
# 
# #### DO Saturation (mg/L and %)
# 
# DO saturation represents the solubility limit of oxygen at specific temperature, salinity, and pressure. GSW's O2sol function implements oxygen solubility equations from Garcia & Gordon (1992), based on Benson & Krause (1984), using TEOS-10 conversions (Absolute Salinity, Conservative Temperature) as described in McDougall and Barker (2011).
# 
# **Calculation:**
# ```
# DO_saturation (mg/L) = gsw.O2sol(SA, CT, P)
# ```
# 
# where:
# - SA = Absolute Salinity (g/kg)
# - CT = Conservative Temperature (°C)
# - P = Sea Pressure (positive dbar, e.g., 10 at 10m depth)
# 
# **Percent Saturation:**
# ```
# DO%_saturation = (DO_measured (mg/L) / DO_saturation (mg/L)) × 100
# ```
# 
# - If DO% > 100%, water is supersaturated with oxygen
# - If DO% < 100%, water is undersaturated
# 
# ---
# 
# #### Partial Pressure of Oxygen (pO₂, kPa)
# 
# The partial pressure of oxygen is directly proportional to its concentration and saturation:
# ```
# pO₂ (kPa) = (DO_measured (mg/L) / DO_saturation (mg/L)) × P_atm × 0.2095
# ```
# 
# where:
# 
# **Atmospheric pressure:**
# - P_atm = 101.3253 kPa (standard atmospheric pressure at sea level, 1.013253 bar)
# 
# **Oxygen mole fraction:**
# - 0.2095 = O₂ mole fraction in atmosphere
# 
# **Critical note:** P_atm (atmospheric pressure only) is used because gsw.O2sol already accounts for depth pressure through the sea_pressure_dbar parameter. Using total pressure (P_atm + P_hydrostatic) would incorrectly double-count pressure effects.
# 
# **Total pressure at depth (calculated for reference, not used in pO₂):**
# ```
# P_total = P_atm + P_hydrostatic
# ```
# **Hydrostatic pressure increase with depth:**
# - P_hydrostatic = P × 10.0 × (density/1025) kPa
# - P = sea pressure (dbar, where 1 dbar = 10 kPa exact)
# - density = in-situ seawater density (kg/m³)
# - 1025 = reference density normalization (accounts for density variations with T, S, P)
# 
# **Example at 10m depth (P ≈ 10 dbar):**
# - Assuming density ≈ 1025 kg/m³
# - P_hydrostatic = 10 × 10.0 × (1025/1025) = 100 kPa
# - P_total = 101.3253 + 100 = 201.3253 kPa
# - Note: P_total is calculated but NOT used in pO₂ calculation
# 
# ---
# 
# #### Apparent Oxygen Utilization (AOU, mg/L)
# 
# Calculated as the difference between calculated saturation value and measured in-situ DO at a given depth (NOAA, 2013):
# ```
# AOU (mg/L) = DO_saturation - DO_measured
# ```
# 
# - AOU > 0 → More oxygen consumed (respiration, oxidation)
# - AOU < 0 → Water supersaturated (photosynthesis, atmospheric mixing)
# 
# ---

# %% [markdown]
# # Initialization,  2014 loading

# %%
## should already be moved to:
#output_dir = '../../../../SSM_output/SSM_data_working'  # Define the output directory where 2014 copy of data to plot is

##requires first to run precursor script : 1_***script*** 

#initialize
import os

import xarray as xr
import pandas as pd
import gsw  # GSW library for oceanographic calculations which uses the update to UNESCO (1981): Thermodynamic Equation of Seawater 2010 (TEOS-10)
#correct Ref:  McDougall, T.J. and P.M. Barker, 2011: Getting started with TEOS-10 and the Gibbs Seawater (GSW) Oceanographic Toolbox, 28pp., SCOR/IAPSO WG127, ISBN 978-0-646-55621-5. (available at https://www.teos-10.org/software.htm)

from helper_ExportsAndFigs               import load_all_nc_datasets     ## loads all netcdf datasets within subdirectories
from helper_ExportsAndFigs               import export_dictionary_of_nc_datasets     ## makes a dir and dataarray.nc of everything in given nested dictionaries

# %%
# #Ref:  McDougall, T.J. and P.M. Barker, 2011: Getting started with TEOS-10 and the Gibbs Seawater (GSW) Oceanographic Toolbox, 28pp., SCOR/IAPSO WG127, ISBN 978-0-646-55621-5. (available at https://www.teos-10.org/software.htm)
# #

##### calculations####################
#DO: conversion of measured/modeled data not needed 
#DOXG_umol_kg = (DOXG_GSW_input_mg_l / 32)                         * 1000                               / density_est_kg_m3  # Dissolved oxygen data input required (μmol/kg)
#              = (DO mg/L / molar mass of O₂ (32 g/mol) for mmol/L) * 1000 for μmol (1 mmol = 1000 μmol) / seawater density (1.025 kg/L)


# %%
### Saturation Solubility and AOU  calculations (3d array) 3.5 min to run for existing and ref for all outputs used
#  NOTE: change min max salinity and temp output names in results  to match what is used for input 

def calculate_saturation_and_aou(DOXG_GSW_input_mg_l, salinity_GSW_input_ppt, temp_GSW_input_C_insitu, sea_pressure_dbar, latitude, longitude):
    # Salinity: Convert Practical Salinity (PS)/Parts Per Thousand (PPT) to Absolute Salinity (SA) (g/kg). Note that Practical Salinity (SP) is dimensionless and assuming equivalent to PPT units.
    salinity_SA_g_kg = gsw.SA_from_SP(salinity_GSW_input_ppt, sea_pressure_dbar, longitude, latitude)  # conversion to salinity data input (g/kg) required for GSW
    #salinity_SA_g_kg = xr.apply_ufunc(
    #        gsw.SA_from_SP, salinity_GSW_input_ppt, sea_pressure_dbar, longitude, latitude,
    #        dask='parallelized', output_dtypes=salinity_GSW_input_ppt.dtype
    #    )  # conversion to salinity data input (g/kg) required for GSW

    # Temperature: data input (°C) insitu from SSM outputs converted to Conservative CT and potential pt
    temp_conservative = gsw.CT_from_t(salinity_SA_g_kg, temp_GSW_input_C_insitu, sea_pressure_dbar)  # Conservative temperature calculation using GSW function See: https://www.teos-10.org/pubs/gsw/html/gsw_CT_from_t.html
    #temp_conservative = xr.apply_ufunc(
    #        gsw.CT_from_t, salinity_SA_g_kg, temp_GSW_input_C_insitu, sea_pressure_dbar,
    #        dask='parallelized', output_dtypes=temp_GSW_input_C_insitu.dtype
    #    )  # Conservative temperature calculation using GSW function See: https://www.teos-10.org/pubs/gsw/html/gsw_CT_from_t.html
    temp_pt_potential = gsw.pt_from_t(salinity_SA_g_kg, temp_GSW_input_C_insitu, sea_pressure_dbar, p_ref=0)  # Not used. Debug? If needed should use default p_ref=0 . See https://www.teos-10.org/pubs/gsw/html/gsw_pt_from_t.html

    # Density estimate: Calculate in-situ density using GSW function in kgm3 - used to calculate P_total_kPa
    density_est_kg_m3 = gsw.rho_t_exact(salinity_SA_g_kg, temp_conservative, sea_pressure_dbar)  # Calculate in-situ density using GSW function

    # Calculate dissolved oxygen solubility using GSW at in-situ conditions and depth See. https://www.teos-10.org/pubs/gsw/html/gsw_O2sol.html#2
    # inputs:
    # SA = Absolute Salinity [ g/kg ]
    # CT = Conservative Temperature [ deg C ]
    # p = sea pressure [(+)dbar ]
    solubility_GSW_output = gsw.O2sol(salinity_SA_g_kg, temp_conservative, sea_pressure_dbar, longitude, latitude)  # solubility in μmol/kg
    # Convert solubility from μmol/kg to mg/L
    # Step 1: μmol/kg → mg/kg using O₂ molar mass (31.998 g/mol)
    # Step 2: mg/kg → mg/L by multiplying by seawater density (kg/L)
    # density_est_kg_m3/1000 = actual seawater density in kg/L, accounts for T,S,P effects
    solubility_GSW_output_mg_l = (solubility_GSW_output * 31.998 / 1000) * (density_est_kg_m3 / 1000)
    # Debug check on above: Step 1: Convert µmol/kg to mol/kg :solubility_mol_per_kg = solubility_umol_per_kg / 10**6; # Step 2: Convert mol/kg to g/kg (using the molar mass of O₂, which is 32 g/mol): solubility_g_per_kg = solubility_mol_per_kg * 32, and #Step 3: Convert g/kg to mg/L (assuming the density of seawater is close to 1 kg/L):solubility_mg_per_L = solubility_g_per_kg * 1000

    # Calculate Apparent Oxygen Utilization (AOU):
    DO_AOE_mg_l = (solubility_GSW_output_mg_l - DOXG_GSW_input_mg_l)  # solubility_GSW_output_mg_l calculated at insitu depth - measured/modeled actual DO at that location
    # Note debug: Not using solubility_GSW_out0bar_mg_l which is an estimate of what solubility would be for that parcel of water at the surface atmospheric pressure without hydrostatic

    # Calculate DO % Saturation using sat_GSW not saturation_GSW_out0bar_mg_l
    DO_percent_saturation = (DOXG_GSW_input_mg_l / solubility_GSW_output_mg_l) * 100

    # Convert DO solubility and concentration (insitu) from mg/L to partial pressure of oxygen (pO₂) in kPa
    # Calculate total pressure at depth (P_total_kPa includes atmospheric + hydrostatic pressure)
    # debug simplified eg. : P_total_kPa = 101.3253 + (sea_pressure_dbar * 10)  # Convert sea pressure from (+) dbar to (+)kPa, assuming atmospheric = 101.3253 kPa
    # Precise conversion factor for dbar to kPa adjusted for in-situ density
    # Calculate total pressure at depth (kPa)
    # P_total = atmospheric + hydrostatic pressure
    # 1 dbar = 10.0 kPa exact conversion, density correction essential for accuracy at depth/temperature extremes
    # Accounts for in-situ density variations
    P_total_kPa = 101.3253 + (sea_pressure_dbar * 10.0 * (density_est_kg_m3 / 1025))  # total pressure accounting for variations in seawater density with depth
    # Input: 101.3253 kPa = Atmospheric pressure at sea level (kPa)+(sea_pressure_dbar (ie hydrostatic (+dbar)) *10.0 kPa/dbar = dbar to kPa, (density_est_kg_m3 = In-situ density of seawater (kg/m³) / # 1025 kg/m³ = Reference density of seawater, used to normalize the in-situ density)
    # print(f"Debug: P_total including atmospheric (101.3253 kpa) and sea_pressure_dbar (hydrostatic) converted to kpa({sea_pressure_dbar}) = {P_total_kPa}, from dbar hydrostatic ({sea_pressure_dbar}) + atmospheric pressure)")  # debug

    # Calculate pO₂ at in-situ depth (kPa)
    # 0.2095 = mole fraction of O₂ in atmosphere
    # gsw.O2sol already accounts for depth pressure via sea_pressure_dbar input
    # P_atm (atmospheric pressure only) used because using P_total would double-count pressure effects
    pO2_insitu_kPa = (DOXG_GSW_input_mg_l / solubility_GSW_output_mg_l) * (101.3253 * 0.2095)  # Uses measured DO and solubility at in-situ depth

    return {
        'salinity_gKg': salinity_SA_g_kg,
        'solubility_GSW_output': solubility_GSW_output_mg_l,
        'DO_AOE_mg_l': DO_AOE_mg_l,
        'DO_percent_saturation': DO_percent_saturation,
        'temp_CT': temp_conservative,
        'pO2_insitu_kPa': pO2_insitu_kPa
    }

# %% [markdown]
# ### Depth averaging of new calculated datasets (using existing 3d dataarrays to create 2d depth averaged in same dictionaries )
def average_or_select_by_depth_dataset(param_dict):
    """
    Averages or selects the data by specific depth for each key in the dictionary containing Datasets making a copy that is effectively 2D vs original 3D.
    Parameters:
        param_dict (dict): Dictionary containing xarray Datasets.
    Returns:
        dict: Updated dictionary with averaged/selected data.
    """
    param_dict_2D = {key: dataset.copy(deep=True) for key, dataset in param_dict.items()}  # Create a deep copy for new  2D version

    for key in param_dict_2D:  # Process the deep copy to create the 2D version
        dataset = param_dict_2D[key]
        print(f"\n Starting on new dataset. Processing key '{key}' with dataset:")
        print(dataset, "\n")
        
        for var_name in dataset.data_vars:  # Each data array inside the dataset
            var_shape = dataset[var_name].shape
            print(f"Processing variable: {var_name} with shape {var_shape}")  # Debugging
            
            if var_shape[1] != 10:
                raise ValueError(f"Error: Variable '{var_name}' in dataset '{key}' has siglay (depth layers) size {var_shape[1]}, expected 10.")
            
            # Extract top layer (_tp)
            dataset[var_name + '_tp'] = dataset[var_name][:, 0, :]  

            # Extract bottom layer (_bt)
            dataset[var_name + '_bt'] = dataset[var_name][:, 9, :]  

            # Extract min across middle layers (_md)
            dataset[var_name + '_md'] = dataset[var_name][:, 1:9, :].min(dim='siglay')

            # Extract average across middle layers (_mA)
            dataset[var_name + '_mA'] = dataset[var_name][:, 1:9, :].mean(dim='siglay')

            # Extract Average across the whole water column (_wA)
            dataset[var_name + '_wA'] = dataset[var_name].mean(dim='siglay')

            # Extract min across the whole water column (_wc)
            dataset[var_name + '_wc'] = dataset[var_name].min(dim='siglay')

            print(f"Added all new data arrays with depth selection/averaging for {var_name}")

        # Remove original 3D variables
        for var_name in list(dataset.data_vars):  # Iterate through all data variables in the dataset
            if dataset[var_name].ndim == 3:  # Check if the variable has three dimensions
                print(f"Lastly, removing variable: {var_name}")  # Debugging: print the name of the variable being removed
                del dataset[var_name]  # Delete the original 3D variable
        
        param_dict_2D[key] = dataset  # Update the dictionary with the modified dataset

    return param_dict_2D  # Return the updated 2D dictionary

# Function to filter by specific nodes (see above to provide first specific nodes from GIS file)
def filter_by_specific_nodes(data_dict, specific_nodes):
    """
    Filter the datasets in the dictionary by specific nodes.

    Parameters:
    data_dict (dict): Dictionary containing xarray Datasets.
    specific_nodes (list): List of specific nodes to filter by (1-based indexing). i.e. row 1 from gis is adjusted to row 0 for the eqiv. in numpy dataset

    Returns:
    dict: New dictionary with filtered datasets.
    """
    specific_nodes_zero_based = [node - 1 for node in specific_nodes]  # Adjust to zero-based indexing
    new_data_dict = {}  # Initialize a new dictionary to store filtered datasets

    # Loop through the keys for datasets and each dataarray variable in the dictionary
    for dataset_name, dataset in data_dict.items():
        new_data_dict[dataset_name] = {}  # Initialize a new dictionary for each dataset
        for var_name, data_array in dataset.items():
            filtered_data = data_array[:, specific_nodes_zero_based]  # Filter by specific nodes
            new_data_dict[dataset_name][var_name] = filtered_data  # Save the filtered data

    return new_data_dict  # Return the new dictionary with filtered datasets

def export_xarray_dict_to_excel(data_dict, dict_name, output_dir):
    """Exports a dictionary of xarray DataArrays to Excel files in the specified output directory.
    Args:   
        data_dict: The actual dictionary of xarray DataArrays to export.
        dict_name: The name of the dictionary (used for folder naming).
        output_dir: The directory path to save the Excel files.
    """
    # Create a folder for the dictionary in the output directory
    dict_folder = os.path.join(output_dir, dict_name)  # Folder name based on dict_name parameter
    os.makedirs(dict_folder, exist_ok=True)  # Create folder if it doesn't exist
    
    # Loop through each key in the dictionary
    for dataset_name, dataset in data_dict.items():  # Loop through datasets
        if not dataset:  # Check if the dataset dictionary is empty
            print(f"Skipping [{dict_name}]['{dataset_name}']: No data variables found")  # Print message with dict_name
            continue  # Skip to the next dataset
        
        excel_file_path = os.path.join(dict_folder, f"{dataset_name}.xlsx")  # Create Excel file path
        
        with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:  # Create Excel writer
            for var_name, data_array in dataset.items():  # Loop through dataarray variables
                df = data_array.to_dataframe()  # Convert data_array to DataFrame
                df = df.reset_index()  # Reset index
                df.to_excel(writer, sheet_name=var_name, index=False)  # Export to Excel sheet
                print(f"Data exported to {excel_file_path} in sheet {var_name}")  # Debug message


def main():
    output_dir = 'SSM_output/SSM_data_working'  # Define the output directory where 2014 copy of data to plot is

    # Specify the subdirectories to load
    subdirectories_to_load = [
        #3D inputs needed for processing saturation and metabolic tec 
        'MinParam_WholeYear10Layers_timeseries_DOX',
        'MaxParam_WholeYear10Layers_timeseries_DOX',
        'MeanParam_WholeYear10Layers_timeseries_DOX',  # Added for mean calculations  #*#
        'MeanParam_WholeYear10Layers_timeseries_sal',  # Used for all calculations
        'MeanParam_WholeYear10Layers_timeseries_temp',  # Used forall calculations
        #2d inputs geometry (no time dim):
        'SSM_geometry_2D',
        #3d xarray to process and export final products
        'Calculated_WholeYear10Layers_3D_Xarray'
    ]
    # Call the function to load all NetCDF datasets from the specified subdirectories
    loaded_datasets = load_all_nc_datasets(output_dir, subdirectories_to_load)

    # Print the loaded datasets for verification
    print(f"The wrapper dictionary loaded_datasets loaded from nc files with a dictionary for each subdirectory and multiple datasets with key names, each with multiple variables/dataarray")
    for subdir, datasets in loaded_datasets.items():
        print(f"Subdirectory: {subdir}")
        for dataset_name, dataset in datasets.items():
            print(f"  Dataset: {dataset_name}")
            #print(dataset)

    # Make 2014 dictionary using result of call to function above
    SSM2014_dic = loaded_datasets
    del loaded_datasets, subdir, datasets, dataset, dataset_name # Cleanup - NOTE: keeping subdirectories_to_load for use in debug subsampling function

    print(f"\nNow separated into individual dictionaries and the loaded_datasets dictionary deleted")
    print(f"Minimal error checking so if you get an error on variables not found to del etc, likely inputs are not in the SSM_output folder as expected\n\n")

    # %%
    #reset main output directory used later in plots:
    output_dir = 'SSM_output/'

    # %% [markdown]
    # # Matrix algebra preparing depth etc for saturation and metabolic index

    # %% [markdown]
    # ### Description 

    # %% [markdown]
    # #### Preparation of geometric calculations
    # Outputs used as solubility and AOE inputs: sea_pressure_dbar, latitude, longitude
    # 
    # SSM model results are independent inputs to solubility and AOE functions and are modified at that point

    # %%
    # pressure caculuated from total (-)depth at lat and long for puget sound for a single input location and single output:

    #NOTE:  DOXG_min or max is NOT used in calculation instead min (DOXG_GSW_input_mg_l) is used here
    # only for its shape (specifically, the size of its time dimension day).

    #inputs
    #take DOX to define the final 3d format to use when expanding the 2d datasets to match 
    DOXG_GSW_input_mg_l = SSM2014_dic['MinParam_WholeYear10Layers_timeseries_DOX']['exist'].DOXG_daily_min_wc  # Dissolved oxygen from SSM (mg/L) 3d array, all dephts
    #  extracting geometry from earlier
    #new inputs to use
    depth_z_m_neg = SSM2014_dic['SSM_geometry_2D']['exist'].mid_depth_from_surface #2D dataarray
    # selected_value = SSM2014_dic['SSM_geometry_2D']['exist'].mid_depth_from_surface.sel(siglay=9, node=13788) #Debug node_id_OrigGis=13789  for Hood canal Orca
    latitude_1D = SSM2014_dic['SSM_geometry_2D']['exist'].latitude_reproj  # 1D
    longitude_1D = SSM2014_dic['SSM_geometry_2D']['exist'].longitude_reproj # 1D
    # Expand latitude along siglay to match the depth array's shape for 2d matrix algebra
    latitude_2D = latitude_1D.expand_dims(siglay=depth_z_m_neg.sizes['siglay']) #pulling .size of siglay (ie 10 depths), then adding that dim , then broadcass same values across all depth levels )
    longitude_2D = longitude_1D.expand_dims(siglay=depth_z_m_neg.sizes['siglay']) #pulling .size of siglay (ie 10 depths), then adding that dim , then broadcass same values across all depth levels )

    # Compute sea pressure 
    sea_pressure_dbar = gsw.p_from_z(depth_z_m_neg, latitude_2D)# broadcast correctly as both same dims

    # Expand all to 3D (matching DOXG_GSW_input_mg_l)
    depth_z_3D = depth_z_m_neg.expand_dims(day=DOXG_GSW_input_mg_l.sizes['day'])
    assert depth_z_3D.dims == ('day','node','siglay'), depth_z_3D.dims
    latitude_3D = latitude_2D.expand_dims(day=DOXG_GSW_input_mg_l.sizes['day'])
    assert latitude_3D.dims == ('day','siglay','node'), latitude_3D.dims
    longitude_3D = longitude_2D.expand_dims(day=DOXG_GSW_input_mg_l.sizes['day'])
    assert longitude_3D.dims == ('day','siglay','node')
    sea_pressure_3D = sea_pressure_dbar.expand_dims(day=DOXG_GSW_input_mg_l.sizes['day'])
    assert sea_pressure_3D.dims == ('day','node','siglay'), sea_pressure_3D.dims

    ## reasign names for next fuction and clean up all other parameters
    sea_pressure_dbar = sea_pressure_3D
    latitude = latitude_3D
    longitude = longitude_3D

    del  DOXG_GSW_input_mg_l, depth_z_m_neg,depth_z_3D, latitude_1D, longitude_1D, latitude_2D, longitude_2D,latitude_3D, longitude_3D,sea_pressure_3D,# Clean up

    # %% [markdown]
    # # Calculation of DO Saturation, DO partial pressure (pO2), and Apparent Oxygen Utilization
    # 
    # 

    # %% [markdown]
    # ### Saturation Solubility and AOU inputs and calculations (sourced from existing SSM dataarrays)

    # %%
    print(f"\nProcessing of saturation 3D files begun\n")  

    # %%
    ##inputs (3d array) 
    #NOTE FOR DEVELOPMENT -AFTER Qa CHANGE TO GET ABSOLUTE DAILY MIN METABOLIC GIVEN TEMP AND SALINITY IDENTIFIED BELOW
    
    ### 

    # %%
    ######################################################
    ### call the saturation function 
    # # Initialize the new parent dictionary
    SSMcalcs_dic = {}  # Root dictionary to store calculated results

    # %%
    ##Min DOX call of function and save of data (Min DOXG, mean salinity, and mean temperature)
    # Note: Select the specific daily salinity and temperature needed here.   Change for min/max/max average 
    #   1)input sources and
    #   2)the function returns generic variable names, and you explicitly rename outputs
    #   3)export call names matching what is produced here

    for key in SSM2014_dic['MinParam_WholeYear10Layers_timeseries_DOX'].keys():  # e.g., keys = exist
        results = calculate_saturation_and_aou(
            DOXG_GSW_input_mg_l = SSM2014_dic['MinParam_WholeYear10Layers_timeseries_DOX'][key].DOXG_daily_min_wc,  
            salinity_GSW_input_ppt = SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_sal'][key].salinity_daily_mean_wc,  
            temp_GSW_input_C_insitu = SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_temp'][key].temp_daily_mean_wc,
            sea_pressure_dbar = sea_pressure_dbar,
            latitude = latitude,
            longitude = longitude)
        print(f"Successfully processed saturation outputs for model run where key is: {key}\n")

        # Explicitly rename results for clarity and traceability
        renamed_results = {
            'salinity_daily_mean_gKg': results['salinity_gKg'],                # <--- Explicitly named for this run as using mean
            'solubility_GSW_output': results['solubility_GSW_output'],
            'DO_AOE_mg_l': results['DO_AOE_mg_l'],
            'DO_percent_saturation': results['DO_percent_saturation'],
            'temp_daily_mean_CT': results['temp_CT'],                          # <--- Explicitly named for this 
            'pO2_daily_min_kPa': results['pO2_insitu_kPa']}    # <--- Explicitly named for this run as producing min pO2 (NOTE: this has to change for max run)

        # Store results in the new child dictionaries
        for result_name, result_value in renamed_results.items():
            new_child_dict = f'CalMinParam_3D_{result_name}'  # Create child dictionary name dynamically based on result_name
            if new_child_dict not in SSMcalcs_dic:
                SSMcalcs_dic[new_child_dict] = {k: ds.copy(deep=True) for k, ds in SSM2014_dic['Calculated_WholeYear10Layers_3D_Xarray'].items()}  # Initialize with template
            SSMcalcs_dic[new_child_dict][key][result_name] = result_value  # Save the new data array

    # Clean up variables not needed for export or rerun
    del results, renamed_results, new_child_dict, result_name, result_value, key

    # %%
    ##Max DOX call of function and save of data (Max DOXG, mean salinity, and mean temperature)
    # Note: Select the specific daily salinity and temperature needed here.   Change for min/max/max average 
    #   1)input sources and
    #   2)the function returns generic variable names, and you explicitly rename outputs
    #   3)export call names matching what is produced here

    for key in SSM2014_dic['MaxParam_WholeYear10Layers_timeseries_DOX'].keys():  # e.g., keys = exist
        results = calculate_saturation_and_aou(
            DOXG_GSW_input_mg_l = SSM2014_dic['MaxParam_WholeYear10Layers_timeseries_DOX'][key].DOXG_daily_max_wc,  
            salinity_GSW_input_ppt = SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_sal'][key].salinity_daily_mean_wc,  
            temp_GSW_input_C_insitu = SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_temp'][key].temp_daily_mean_wc,
            sea_pressure_dbar = sea_pressure_dbar,
            latitude = latitude,
            longitude = longitude)
        print(f"Successfully processed saturation outputs for model run where key is: {key}\n")

        # Explicitly rename results for clarity and traceability
        renamed_results = {
            'salinity_daily_mean_gKg': results['salinity_gKg'],                # <--- Explicitly named for this run as using mean
            'solubility_GSW_output': results['solubility_GSW_output'],
            'DO_AOE_mg_l': results['DO_AOE_mg_l'],
            'DO_percent_saturation': results['DO_percent_saturation'],
            'temp_daily_mean_CT': results['temp_CT'],                          # <--- Explicitly named for this 
            'pO2_daily_max_kPa': results['pO2_insitu_kPa']}    # <--- Explicitly named for this run as producing max pO2

        # Store results in the new child dictionaries
        for result_name, result_value in renamed_results.items():
            new_child_dict = f'CalMaxParam_3D_{result_name}'  # Create child dictionary name dynamically based on result_name
            if new_child_dict not in SSMcalcs_dic:
                SSMcalcs_dic[new_child_dict] = {k: ds.copy(deep=True) for k, ds in SSM2014_dic['Calculated_WholeYear10Layers_3D_Xarray'].items()}  # Initialize with template
            SSMcalcs_dic[new_child_dict][key][result_name] = result_value  # Save the new data array

    # Clean up variables not needed for export or rerun
    del results, renamed_results, new_child_dict, result_name, result_value, key

    # %%
    ##Mean DOX call of function and save of data (Mean DOXG, mean salinity, and mean temperature)
    # Note: Select the specific daily salinity and temperature needed here.   Change for min/max/max average 
    #   1)input sources and
    #   2)the function returns generic variable names, and you explicitly rename outputs
    #   3)export call names matching what is produced here

    for key in SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_DOX'].keys():  # e.g., keys = exist
        results = calculate_saturation_and_aou(
            DOXG_GSW_input_mg_l = SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_DOX'][key].DOXG_daily_mean_wc,  
            salinity_GSW_input_ppt = SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_sal'][key].salinity_daily_mean_wc,  
            temp_GSW_input_C_insitu = SSM2014_dic['MeanParam_WholeYear10Layers_timeseries_temp'][key].temp_daily_mean_wc,
            sea_pressure_dbar = sea_pressure_dbar,
            latitude = latitude,
            longitude = longitude)
        print(f"Successfully processed saturation outputs for model run where key is: {key}\n")

        # Explicitly rename results for clarity and traceability
        renamed_results = {
            'salinity_daily_mean_gKg': results['salinity_gKg'],                # <--- Explicitly named for this run as using mean
            'solubility_GSW_output': results['solubility_GSW_output'],
            'DO_AOE_mg_l': results['DO_AOE_mg_l'],
            'DO_percent_saturation': results['DO_percent_saturation'],
            'temp_daily_mean_CT': results['temp_CT'],                          # <--- Explicitly named for this 
            'pO2_daily_mean_kPa': results['pO2_insitu_kPa']}    # <--- Explicitly named for this run as producing mean pO2

        # Store results in the new child dictionaries
        for result_name, result_value in renamed_results.items():
            new_child_dict = f'CalMeanParam_3D_{result_name}'  # Create child dictionary name dynamically based on result_name
            if new_child_dict not in SSMcalcs_dic:
                SSMcalcs_dic[new_child_dict] = {k: ds.copy(deep=True) for k, ds in SSM2014_dic['Calculated_WholeYear10Layers_3D_Xarray'].items()}  # Initialize with template
            SSMcalcs_dic[new_child_dict][key][result_name] = result_value  # Save the new data array

    # Clean up variables not needed for export or rerun
    del results, renamed_results, new_child_dict, result_name, result_value, key

    # %%
    print(f"\nCompleted processing of all saturation 3D files ready to export\n")  

    # %%
    #cleanup after saturation function complete and before export
    #clean up remaining variables not needed for filtering onward
    del latitude, longitude, sea_pressure_dbar

    for key in list(SSM2014_dic.keys()):  # Iterate over keys in SSM2014_dic
        if key != 'Calculated_WholeYear10Layers_3D_Xarray': del SSM2014_dic[key]  # Delete all keys in input dictionary (not SSMcalcs_dic with outputs) except the specified one here (delete sourcefiles used eg'MinParam_WholeYear10Layers_timeseries_DOX')

    # %% [markdown]
    # ### export 3d saturation outputs

    # %%
    ## Export all output files to netCDF format for 3D saturation calculations  - NOTE:comment/uncomment mean data if mean DO available 
    #Export function any dictionary of any dataset and datarray to directory and *.nc 
    # from helper_ExportsAndFigs               import export_dictionary_of_nc_datasets     ## makes a dir and dataarray.nc of everything in given nested dictionaries
    output_dir_export_nc = f'{output_dir}/SSM_saturation'
    encoding = {'zlib': True, 'complevel': 4} #set 0 for no compression (few seconds) vs 4 reasonable (30sec) and 9 (took 1 min but abut same size as 4)
    #for plotting only:
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMinParam_3D_salinity_daily_mean_gKg'], dictionary_name="CalMinParam_3D_salinity_daily_mean_gKg", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMinParam_3D_solubility_GSW_output'], dictionary_name="CalMinParam_3D_solubility_GSW_output", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMinParam_3D_DO_AOE_mg_l'], dictionary_name="CalMinParam_3D_DO_AOE_mg_l", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMinParam_3D_DO_percent_saturation'], dictionary_name="CalMinParam_3D_DO_percent_saturation", output_dir=output_dir_export_nc, encoding=encoding)
    #used in metabolic calculations following:
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMinParam_3D_temp_daily_mean_CT'], dictionary_name="CalMinParam_3D_temp_daily_mean_CT", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMinParam_3D_pO2_daily_min_kPa'], dictionary_name="CalMinParam_3D_pO2_daily_min_kPa", output_dir=output_dir_export_nc, encoding=encoding)

    # Max DOX sat Export
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMaxParam_3D_salinity_daily_mean_gKg'], dictionary_name="CalMaxParam_3D_salinity_daily_mean_gKg", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMaxParam_3D_solubility_GSW_output'], dictionary_name="CalMaxParam_3D_solubility_GSW_output", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMaxParam_3D_DO_AOE_mg_l'], dictionary_name="CalMaxParam_3D_DO_AOE_mg_l", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMaxParam_3D_DO_percent_saturation'], dictionary_name="CalMaxParam_3D_DO_percent_saturation", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMaxParam_3D_temp_daily_mean_CT'], dictionary_name="CalMaxParam_3D_temp_daily_mean_CT", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMaxParam_3D_pO2_daily_max_kPa'], dictionary_name="CalMaxParam_3D_pO2_daily_max_kPa", output_dir=output_dir_export_nc, encoding=encoding)

    # Mean DOX sat Export
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMeanParam_3D_salinity_daily_mean_gKg'], dictionary_name="CalMeanParam_3D_salinity_daily_mean_gKg", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMeanParam_3D_solubility_GSW_output'], dictionary_name="CalMeanParam_3D_solubility_GSW_output", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMeanParam_3D_DO_AOE_mg_l'], dictionary_name="CalMeanParam_3D_DO_AOE_mg_l", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMeanParam_3D_DO_percent_saturation'], dictionary_name="CalMeanParam_3D_DO_percent_saturation", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMeanParam_3D_temp_daily_mean_CT'], dictionary_name="CalMeanParam_3D_temp_daily_mean_CT", output_dir=output_dir_export_nc, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSMcalcs_dic['CalMeanParam_3D_pO2_daily_mean_kPa'], dictionary_name="CalMeanParam_3D_pO2_daily_mean_kPa", output_dir=output_dir_export_nc, encoding=encoding)
    del output_dir_export_nc ,encoding# cleanup
    print(f"\nCompleted export of saturation 3D files\n")  

    # %% [markdown]
    # # Filtering saving as 2d as well as excel(everything below is repeated process for datasets in scripts folloiwng )

    #shared inputs for call: 
    output_dir_export_nc = f'{output_dir}/SSM_saturation'  # Define the output directory for export
    encoding = {'zlib': True, 'complevel': 4}  # Set compression level for export
    #call:
    for key in list(SSMcalcs_dic.keys()):  # Iterate over a list of keys from the dictionary
        if '3D' in key:  # Check if the key contains '3D'
            corresponding_2D_key = key.replace('3D', '2D')  # Replace '3D' with '2D' to create the new key
            SSMcalcs_dic[corresponding_2D_key] = average_or_select_by_depth_dataset(SSMcalcs_dic[key])  # Calculate the 2D dataset and assign it to the new key
            del SSMcalcs_dic[key]  # Delete the original 3D key to free up memory
            # Export the 2D dataset
            export_dictionary_of_nc_datasets(
                dictionary_of_nc_datasets=SSMcalcs_dic[corresponding_2D_key],  # created 2d dataset to export
                dictionary_name=corresponding_2D_key,  # Name of the dataset
                output_dir=output_dir_export_nc,  # Output directory
                encoding=encoding  # Compression settings
            )

    # Debug:
    # SSMcalcs_dic['CalMaxParam_2D_temp_daily_mean_CT'] = average_or_select_by_depth_dataset(SSMcalcs_dic['CalMaxParam_3D_temp_daily_mean_CT'])
    # del SSMcalcs_dic['CalMaxParam_3D_temp_daily_mean_CT']  # del 3D to clean up memory

    # SSMcalcs_dic['CalMaxParam_2D_pO2_insitu_kPa'] = average_or_select_by_depth_dataset(SSMcalcs_dic['CalMaxParam_3D_pO2_insitu_kPa'])
    # del SSMcalcs_dic['CalMaxParam_3D_pO2_insitu_kPa']  # del 3D to clean up memory

    # SSMcalcs_dic['CalMinParam_2D_temp_daily_mean_CT'] = average_or_select_by_depth_dataset(SSMcalcs_dic['CalMinParam_3D_temp_daily_mean_CT'])
    # del SSMcalcs_dic['CalMinParam_3D_temp_daily_mean_CT']  # del 3D to clean up memory

    # SSMcalcs_dic['CalMinParam_2D_pO2_insitu_kPa'] = average_or_select_by_depth_dataset(SSMcalcs_dic['CalMinParam_3D_pO2_insitu_kPa'])
    # del SSMcalcs_dic['CalMinParam_3D_pO2_insitu_kPa']  # del 3D to clean up memory

    # SSMcalcs_dic['CalMinParam_2D_Mindex_median'] = average_or_select_by_depth_dataset(SSMcalcs_dic['CalMinParam_3D_Mindex_median'])
    # del SSMcalcs_dic['CalMinParam_3D_Mindex_median']  # del 3D to clean up memory

    # Move the 2D version back into SSM2014_dic
    #SSM2014_dic['Calculated_timeseries_2D_Xarray'] = Calculated_timeseries_2D_Xarray


    #del Calculated_timeseries_2D_Xarray # Delete the temporary variable to avoid unnecessary copies

    # %%
    print(f"\nCompleted filter and export of saturation 2D files\n")  

    #Filter the datasets in the dictionary by specific nodes.

    ############################################################

    # call: filter_by_specific_nodes function  (NOTE this is the original GIS node number, function -1 correctly converts to zero based indexing numpy array to select equiv.)
    #specific_nodes = [8841,13789,14409]  # Specific nodes (1 based indexing included in functionso can give direct GIS node no here as input) for testing as is Penn Cove entrance with single depth of 14m modeled depth used from SSM source file
    specific_nodes = [13789]  # Specific nodes (1 based indexing) for testing as is Penn Cove entrance with single depth of 14m modeled depth used from SSM source file
    #specific_nodes = [8841]  # Specific nodes (1 based indexing) for testing as is Penn Cove entrance with single depth of 14m modeled depth used from SSM source file
    #specific_nodes = [8841, 13789, 9001, 8999, 9164, 10431, 11125, 9707, 8836, 8310, 9413, 8658]  # Specific nodes (1 based indexing) #all except 13789 (ORCA_Twanoh @ hood canal) and 14409 (ORCA CRR001 @ Carr inlet in South Sound) are KC
    #use 8841 for testing as is Penn Cove entrance

    SSMcalcs_dic_excel_for_specific_nodes = {}# Initialize new dictionary

    # Loop through each key in the original dictionary and call the function and save an filtered version for specific nodes 
    for key in SSMcalcs_dic.keys():  # Iterate over keys in SSM2014_dic
        new_key = key + "_SpecificNodes"  # Create new key name by appending "_SpecificNodes"
        SSMcalcs_dic_excel_for_specific_nodes[new_key] = filter_by_specific_nodes(SSMcalcs_dic[key], specific_nodes)  # Apply filter function and assign to new key

    # %%
    #exporting the data:

    # Example usage of export_xarray_dict_to_excel function
    output_dir_excel = f'{output_dir}/Excel_export_specific_node'  # Output directory for Excel export

    # Loop through each key in the filtered dictionary and export to Excel
    for key in SSMcalcs_dic_excel_for_specific_nodes.keys():  # Iterate over keys in SSMcalcs_dic_excel_for_specific_nodes
        export_xarray_dict_to_excel(data_dict=SSMcalcs_dic_excel_for_specific_nodes[key], dict_name=key, output_dir=output_dir_excel)  # Pass the actual dictionary and key name

    # %%
    print(f"\nCompleted export of saturation excel files and script complete\n")  

if __name__ == '__main__': main()
