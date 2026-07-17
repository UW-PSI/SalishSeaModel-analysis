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

import os
import time
from pathlib import Path
import logging
import argparse

import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import gsw  # GSW library for oceanographic calculations which uses the update to UNESCO (1981): Thermodynamic Equation of Seawater 2010 (TEOS-10)
#correct Ref:  McDougall, T.J. and P.M. Barker, 2011: Getting started with TEOS-10 and the Gibbs Seawater (GSW) Oceanographic Toolbox, 28pp., SCOR/IAPSO WG127, ISBN 978-0-646-55621-5. (available at https://www.teos-10.org/software.htm)

from ssm_utils import read_case, FileFinder, DepthReducer
from ssm_utils.modelio import VAR_ATTRS

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

def calculate_saturation_and_aou(DOXG_GSW_input_mg_l, salinity_SA_g_kg, temp_conservative, sea_pressure_dbar, latitude, longitude):
    #temp_pt_potential = gsw.pt_from_t(salinity_SA_g_kg, temp_GSW_input_C_insitu, sea_pressure_dbar, p_ref=0)  # Not used. Debug? If needed should use default p_ref=0 . See https://www.teos-10.org/pubs/gsw/html/gsw_pt_from_t.html

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
        'solubility_GSW_output': solubility_GSW_output_mg_l,
        'DO_AOE_mg_l': DO_AOE_mg_l,
        'DO_percent_saturation': DO_percent_saturation,
        'pO2_insitu_kPa': pO2_insitu_kPa
    }

def DO_saturation(case, ssm_config):
    output_dir = Path(ssm_config['paths']['processed_output']) / case

    logger = logging.getLogger('DO_saturation')

    # Define dimension sizes and load shapefile
    shp = ssm_config['paths']['shapefile']
    gdf = gpd.read_file(shp).set_index('tce')
    if len(gdf) == 16013:
        logger.warning('Correcting shapefile length')
        gdf = gdf.iloc[:-1].copy()

    ff_doxg = FileFinder(case=case, ssm_config=ssm_config)
    ff_temp = FileFinder(case=case, ssm_config=ssm_config, vtype='temp')
    ff_salinity = FileFinder(case=case, ssm_config=ssm_config, vtype='salinity')
    ff_ct = FileFinder(case=case, ssm_config=ssm_config, vtype='CT',
                       check_exists=False)
    ff_po2 = FileFinder(case=case, ssm_config=ssm_config, vtype='pO2',
                        check_exists=False)

    # Input data dictionaries keyed by run type, then min/max/mean
    doxg = {}
    temp = {}
    salinity = {}
    ds_attrs = {}
    for run_type in ff_doxg.run_types:
        doxg[run_type] = {}
        # DOXG
        logger.info(f'Reading DOXG for {run_type}')
        for agg in ('min','mean','max'):
            p = ff_doxg.get_file(run_type, agg)
            with xr.open_dataset(p) as ds:
                if not len(ds_attrs):
                    ds_attrs = ds.attrs
                doxg[run_type][agg] = ds[ff_doxg.get_var_name(p)]
        # Temp - mean only
        logger.info(f'Reading temp for {run_type}')
        p = ff_temp.get_file(run_type, 'mean')
        with xr.open_dataset(p) as ds:
            temp[run_type] = {'mean': ds[ff_temp.get_var_name(p)] }
        # Salinity - mean only
        logger.info(f'Reading salinity for {run_type}')
        p = ff_salinity.get_file(run_type, 'mean')
        with xr.open_dataset(p) as ds:
            salinity[run_type] = { 'mean': ds[ff_salinity.get_var_name(p)] }
    (ndays,nlevels,nnodes) = salinity[run_type]['mean'].shape

    logger.info("All data loaded")

    # # Matrix math preparing depth etc for saturation and metabolic index

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

    #  extracting geometry from earlier
    #new inputs to use
    dr = DepthReducer(ssm_config, gdf)
    depth_z_m_neg = xr.DataArray(np.broadcast_to(dr.zz, (nnodes,nlevels)).T * gdf['depth'].to_numpy() * -1000, dims=('siglay','node'))
    ## Transformation to get the centroid coordinates from shape file
    gdf_latlon = gpd.GeoDataFrame({
        'geometry': gdf.geometry.centroid
    }, crs=gdf.crs, index=gdf.index).to_crs('epsg:4326')
    latitude_1D = xr.DataArray(gdf_latlon.geometry.y, dims='node')
    longitude_1D = xr.DataArray(gdf_latlon.geometry.x, dims='node')
    # Expand latitude along siglay to match the depth array's shape for 2d matrix
    latitude_2D = latitude_1D.expand_dims(siglay=nlevels)
    longitude_2D = longitude_1D.expand_dims(siglay=nlevels)

    # Compute sea pressure
    sea_pressure_dbar = gsw.p_from_z(depth_z_m_neg, latitude_2D).expand_dims(day=ndays)
    assert sea_pressure_dbar.dims == ('day','siglay','node'), sea_pressure_dbar.dims

    # Expand all to 3D (matching DOXG_GSW_input_mg_l)
    depth_z_3D = depth_z_m_neg.expand_dims(day=ndays)
    assert depth_z_3D.dims == ('day','siglay','node'), depth_z_3D.dims
    latitude_3D = latitude_2D.expand_dims(day=ndays)
    assert latitude_3D.dims == ('day','siglay','node'), latitude_3D.dims
    longitude_3D = longitude_2D.expand_dims(day=ndays)
    assert longitude_3D.dims == ('day','siglay','node')

    # %% [markdown]
    # # Calculation of DO Saturation, DO partial pressure (pO2), and Apparent Oxygen Utilization

    # %% [markdown]
    # ### Saturation Solubility and AOU inputs and calculations (sourced from existing SSM dataarrays)

    logger.info("Processing of saturation 3D files begun")  

    ##inputs (3d array) 
    #NOTE FOR DEVELOPMENT -AFTER Qa CHANGE TO GET ABSOLUTE DAILY MIN METABOLIC GIVEN TEMP AND SALINITY IDENTIFIED BELOW

    ### 

    encoding = {'zlib': True, 'complevel': 4} #set 0 for no compression (few seconds) vs 4 reasonable (30sec) and 9 (took 1 min but abut same size as 4)

    ##Min DOX call of function and save of data (Min DOXG, mean salinity, and mean temperature)
    # Note: Select the specific daily salinity and temperature needed here.   Change for min/max/max average 
    #   1)input sources and
    #   2)the function returns generic variable names, and you explicitly rename outputs
    #   3)export call names matching what is produced here

    for run_type in ff_doxg.run_types:
        # Salinity: Convert Practical Salinity (PS)/Parts Per Thousand (PPT) to Absolute Salinity (SA) (g/kg). Note that Practical Salinity (SP) is dimensionless and assuming equivalent to PPT units.
        salinity_SA_g_kg = gsw.SA_from_SP(salinity[run_type]['mean'], sea_pressure_dbar, longitude_3D, latitude_3D)  # conversion to salinity data input (g/kg) required for GSW
        #salinity_SA_g_kg = xr.apply_ufunc(
        #        gsw.SA_from_SP, salinity_GSW_input_ppt, sea_pressure_dbar, longitude, latitude,
        #        dask='parallelized', output_dtypes=salinity_GSW_input_ppt.dtype
        #    )  # conversion to salinity data input (g/kg) required for GSW

        # Temperature: data input (°C) insitu from SSM outputs converted to Conservative CT and potential pt
        temp_conservative = gsw.CT_from_t(salinity_SA_g_kg, temp[run_type]['mean'], sea_pressure_dbar)  # Conservative temperature calculation using GSW function See: https://www.teos-10.org/pubs/gsw/html/gsw_CT_from_t.html
        #temp_conservative = xr.apply_ufunc(
        #        gsw.CT_from_t, salinity_SA_g_kg, temp_GSW_input_C_insitu, sea_pressure_dbar,
        #        dask='parallelized', output_dtypes=temp_GSW_input_C_insitu.dtype
        #    )  # Conservative temperature calculation using GSW function See: https://www.teos-10.org/pubs/gsw/html/gsw_CT_from_t.html
        # Save conservative temperature as we need it for metabolic index
        ct_out_file = ff_ct.get_file(run_type, 'mean')
        ct_ds = xr.Dataset({
            ff_ct.get_var_name(ct_out_file): temp_conservative.assign_attrs(VAR_ATTRS['CT'])
        }, attrs=ds_attrs)
        ct_out_file.parent.mkdir(parents=True, exist_ok=True)
        ct_ds.to_netcdf(ct_out_file, encoding={ff_ct.get_var_name(ct_out_file): encoding })

        for agg in ('min','mean','max'):
            # Now do the pO2 calculation
            results = calculate_saturation_and_aou(
                doxg[run_type][agg],
                salinity_SA_g_kg,
                temp_conservative,
                sea_pressure_dbar = sea_pressure_dbar,
                latitude = latitude_3D,
                longitude = longitude_3D)
            # Save it to a netcdf file
            po2_out_file = ff_po2.get_file(run_type, agg)
            po2_ds = xr.Dataset({
                ff_po2.get_var_name(po2_out_file): results['pO2_insitu_kPa'].assign_attrs(VAR_ATTRS['pO2'])
            }, attrs=ds_attrs)
            po2_out_file.parent.mkdir(parents=True, exist_ok=True)
            po2_ds.to_netcdf(po2_out_file, encoding={ff_po2.get_var_name(po2_out_file): encoding })
        logger.info(f"Successfully processed saturation outputs for model run {run_type}")

def main():
    parser = argparse.ArgumentParser(description='Compute pO2 and conservative temperatures')
    parser.add_argument('case', help='Case file or name')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet; suppress most output')
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO)

    ssm_config, case = read_case(args.case)

    # Start time counter
    start = time.perf_counter()

    DO_saturation(case, ssm_config)

    # End time counter
    end = time.perf_counter()
    logger.info(f'Execution time: {(end - start)/60:.3f} minutes')

if __name__ == '__main__': main()
