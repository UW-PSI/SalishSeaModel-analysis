#!/usr/bin/env python3

#### 2025.07.19  Mazzilli  -rerun for vs2 of MI with all inuts includig Mean and max and min do
#### Script: 1_DO_Saturation_load_save_7 *.ipynb  
#### Loads, subsamples, and processes source* Salish Sea Model (SSM) 3D NetCDF output for: dissolved oxygen (DO), temperature, salinity, nutrients, and phytoplankton, and exports standardized xarray Datasets for further analysis.
##### *Note these are *.nc files from prior phase 1 King county processing of raw data .out  
#### Handles all years and multiple model runs, with flexible support for additional variables.

"""
## Summary
**Purpose:**  
- Load and subsample 3D SSM NetCDF outputs (DO, temp, salinity, NH4, NO3, B1, B2) for all model runs and years.
- Standardize data structure, add coordinates and attributes, and export as NetCDF for downstream scripts.

---

## Key Steps

**1. Data Loading:**  
- Loads NetCDF datasets for each variable and model run using `xarray.open_dataset`.
- Subsamples nodes using shapefile-based selection (`tce` column in `gdf`).
- **Key variables:**  
  - `MinParam`, `MaxParam`, `MeanParam` (dictionaries of DataArrays for each variable and run)
  - Example: `MinParam['exist'] = DOXG_daily_min_wc[time, depth, node]`

**2. DataArray to Dataset Conversion:**  
- Converts each DataArray dictionary to a Dataset dictionary using `convert_dataarray_dict_to_dataset_dict`.
- **Key variables:**  
  - `MinParam_timeseries_DOX`, `MeanParam_timeseries_temp`, etc.
  - Example: `MinParam_timeseries_DOX['exist']['DOXG_daily_min_wc']`

**3. Add Coordinates:**  
- Adds time, depth, node, latitude, longitude, and total depth as coordinates using `process_and_add_coordinates`.
- **Key variables:**  
  - `MinParam_timeseries_DOX` (now with coordinates)
  - Coordinates from shapefile: `latitude_reproj`, `longitude_reproj`, `total_depth_m`

**4. Add Attributes:**  
- Assigns descriptive attributes (long_name, units) to each variable using `add_specific_attributes`.
- **Key variables:**  
  - `MinParam_timeseries_DOX['exist']['DOXG_daily_min_wc'].attrs`

**5. Depth Averaging/Selection:**  
- Reduces 3D arrays to 2D by extracting top (`_tp`), bottom (`_bt`), and water column min/avg (`_wc`, `_wA`) using `average_or_select_by_depth_dataset`.
- **Key variables:**  
  - `MinParam_timeseries_DOX['exist']['DOXG_daily_min_tp']` (top layer)
  - `MinParam_timeseries_DOX['exist']['DOXG_daily_min_bt']` (bottom layer)
  - `MinParam_timeseries_DOX['exist']['DOXG_daily_min_wc']` (min across all depths)
  - `MinParam_WholeYear10Layers_timeseries_DOX` (full 3D, all layers)

**6. Geometry and Template Datasets:**  
- Creates geometry/template datasets for use in downstream scripts.
- **Key variables:**  
  - `SSM_geometry_2D['exist']['mid_depth_from_surface']`
  - `Calculated_WholeYear10Layers_3D_Xarray['exist']` (template for calculations)

**7. Export:**  
- Exports all processed Datasets as NetCDF files using `export_dictionary_of_nc_datasets`.
- **Key variables:**  
  - Output files for each processed dictionary and geometry/template dataset.

---

## Input/Output Directories and File Naming

**Input Example:**  
- `/SSM_data_working/MinParam_WholeYear10Layers_timeseries_DOX/exist.nc`, DataArray: `DOXG_daily_min_wc`

**Output Examples:**  
- NetCDF: `/SSM_output/SSM_data_working/MinParam_timeseries_DOX/exist.nc`
- NetCDF (full 3D): `/SSM_output/SSM_data_working/MinParam_WholeYear10Layers_timeseries_DOX/exist.nc`
- Geometry: `/SSM_output/SSM_data_working/SSM_geometry_2D/exist.nc`

---

## Data Structure Notes
- Dictionaries like `MinParam_timeseries`, `MaxParam_timeseries`, and `MeanParam_timeseries` contain xarray Datasets for each model run.
- Each Dataset holds DataArrays named by variable and depth selection, e.g., `DOXG_daily_min_wc`, `temp_daily_min_tp`.
- Depth dimension (`siglay`) convention:
  - `_tp`: Top layer (index 0)
  - `_bt`: Bottom layer (index 9)
  - `_wc`: Minimum across all depths
  - `_wA`: Average across all depths
- Example:  
  `MinParam_timeseries_DOX['exist']['DOXG_daily_min_wc']` has shape `(time, depth, node)`.

**Note:** Input folders must only contain expected `.nc` files—other file types may cause errors.
"""

import os
from pathlib import Path

import pandas as pd
import xarray as xr
import numpy as np

# load functions from my helper scripts (must be in same directory and *.py)
from ssm_utils import read_case
from helper_variable_name_datasetreview import generate_new_name, Variable_naming, review_dictionary #  helper file calling variable and plot text manipulation functions
from helper_variable_name_datasetreview import review_dictionary                                     # same  helper file calling dictionary and data review function
from helper_variable_name_datasetreview import clean_shapefile_check16012_len                        # same  helper file calling shape file and geopandas functions
#  NEED TO ADD THESE BACK IN BUT CURRENTLY DIRECTLY HERE XYX from helper_variable_name_datasetreview import add_coordinates_to_dataset                            # add dataset coordinates function 1
#from helper_variable_name_datasetreview import process_and_add_coordinates        #needs to be added back in after update                   # add dataset coordinates function 2
from helper_ExportsAndFigs               import export_xarray_to_excel               ## makes a pandas and then excel of  a specified dataarray
from helper_ExportsAndFigs               import export_dictionary_of_nc_datasets     ## makes a dir and dataarray.nc of everything in given nested dictionaries
from helper_ExportsAndFigs               import plot_parameter_depth              ## Plot and export planar plot of depths (+m input)
from helper_ExportsAndFigs               import plot_parameter_DOXG                  ## Plot and export planar plot of DOXG
from helper_ExportsAndFigs               import plot_parameter_DOXG_dif              ## Plot and export planar plot of DOXG dif exis-ref

def load_nc(ssm, case, gdf, model_var, aggtype='mean'):
    ### DEFINE DATA DIR PATH PATH AND DISPLAY ALL VARIABLES DEFINED  
    # define model_var and associated folder for path to get that  model output (original location,
    # define the data directory (using above yaml file extraction or direct ref) 
    processed_netcdf_dir = Path(ssm['paths']['processed_output'])/case/ model_var
    dir_list = os.listdir(processed_netcdf_dir) # Get list of run sub-directories in processed netcdf directory

    # Function: Loading all run nc files (currently no combining of datasets  eg NH4 and NO3 separate)

    # Steps a)Load and iterate on all runs in selected parameter folder eg DOXG (EG RUN_DIR finds all folders in 'whidbey then loops for bottom, wC etc)  - opening the *.nc run_file with xarray
            # NOTE: just for WC as subsampling this later forbottom and top etc -orriginal code usedif scope=benthic etc
#       b) subsample to process (currently no subsampling set)
#       c) make the working array eg. MinParam which currently contains min,  or MaxParm for max etc
        ### no error checking for if a) code has been run and will error as dims now 2 not 3 for wc average, b) there is a text file in whidbey or in the parameter (eg DOX directory), this causes a file not found with xarray type error until they are removed 
        ### however will catch below "file not found" and skips if eg text directory or I have added entry for existing - ref

    # Initialize dictionaries
    Param={}

    ### define the nodes to subset or use TCE for all- Define this in shape file column with 1 for those to include and 0 to exclude: 
    #gdf_shp_column_for_subselection = 'included_i' #using include_1 reduces to 4144 (note this adds 10min to run just min_param matrix algebra later??), excluding all not WA waters and all non masked waters 
    gdf_shp_column_for_subselection = 'tce'  # so instead just using tce keeps all Salish Sea domain 16012 nodes/cells ad will NaN masked area later
    select_nodes_that_are_not_zero = gdf[gdf_shp_column_for_subselection][gdf[gdf_shp_column_for_subselection] != 0] # Filter out zero indices and already  zero-based indexing(checked and tce first value  1 so need ot   -1 code below to make zero base)

    for run_dir in dir_list:
        try: 
            ## adding daily_min nc dataset -hard coded
            run_file=processed_netcdf_dir/run_dir/'wc'/f'daily_{aggtype}_{model_var}_wc.nc'
            print(f'next run_file used in {run_dir} for water column datasource is:',run_file)
            with xr.open_dataset(run_file) as ds:
                print(f'list of variables in the run_file:{[*ds]}') # Print the list of variables in the dataset to inspect its contents
                Param_full=ds[f'{model_var}_daily_{aggtype}_wc'] # Extract the 'daily minimum' for the   water column(10 layers) and put in xarray  dataset
                print(f'{aggtype}_full array made from run file,with shape before subsample: {Param_full.shape}')
                Param[run_dir]=Param_full[:,:,select_nodes_that_are_not_zero -1] # Sub-sample nodes from the full dataset using the 'tce' column from the GeoDataFrame 'gdf' tce see below 
                                                                    # The 'tce' column contains node indices; subtract 1 to adjust for zero-based indexing
                                                                    # using tce keeps 16012, using include_1 reduces to 4144, excluding all not WA waters and all non masked waters rThis reduces the number of nodes from 16012 to 7494? by selecting specific indices. ### However, still appears to be 16012 -SM to address as in Tce_1 in my copy
                print(f'Final {aggtype}Param array shape (insideof MinParam dic) after subsample: {Param[run_dir].shape}\n')   # Print the shape of the sub-sampled data array to verify its dimensions
        except FileNotFoundError:
            print(f'File Not Found when looking for daily {aggtype} or maybe other files unexpected in folder, so should skip it and go to next run_dir: {run_file}\n')
    
    # Convert to Datasets
    return {key: value.to_dataset() for key, value in Param.items()}

# Function: Add coordinates to datasets
def add_coordinates_to_dataset(dataset, coords):
    """ Adds multiple coordinates per dimension to a Dataset, ensuring flexibility.
    Args:
        dataset (xarray.Dataset): The Dataset to add coordinates to.
        coords (dict): A dictionary where keys are dimension names and values are dicts of coordinates.
    Returns:
        xarray.Dataset: The Dataset with added coordinates.
    """
    # Iterate through each dimension's coordinates
    for dim, coord_dict in coords.items():  #Now supports multiple coordinates per dimension
        if dim in dataset.dims and isinstance(coord_dict, dict):  # Ensure it’s a dictionary
            print(f"# Debug: Adding multiple coordinates for dimension '{dim}'")
            dataset = dataset.assign_coords(coord_dict)  #Assign all coordinates at once

    return dataset

def process_and_add_coordinates(dic_add_coordinates, coords):
    """ Iterates through the dictionary of datasets and processes each variable to add coordinates.
    Args:
        dic_add_coordinates (dict): Dictionary containing datasets to process.
        coords (dict): Dictionary specifying multiple coordinates for each dimension.
    Returns:
        dict: Updated dictionary with datasets containing added coordinates.
    """
    for key in dic_add_coordinates:
        dataset = dic_add_coordinates[key]

        # Iterate over each variable in the dataset
        for var_name in dataset.data_vars:
            var_dataset = xr.Dataset({var_name: dataset[var_name]})  # Isolating the variable

            # Apply coordinates
            dataset_with_coords = add_coordinates_to_dataset(var_dataset, coords)  # CHANGED: Now supports multiple per dimension

            # Replace the old dataset with the new version (with coordinates)
            dic_add_coordinates[key][var_name] = dataset_with_coords[var_name]

    return dic_add_coordinates

##########Matrix algebra for selection and average (eg bottom = bt, surface = tp, Water Column =wc)  within the depths 10 layers to remove depth dimension (siglay) - Dictionary with Dataset of data arrays (_timeseries) not dictionary of dataarray directly (eg. ) 
### currently _wc is the minimum of the water column while _wA is the average of the water column and _wX is the maximum of the water colum
def average_or_select_by_depth_dataset(param_dict):# Iterate over each key in the dictionary
    """
    Averages or selects the data by specific depth for each key in the dictionary containing Datasets.
    Parameters:    param_dict (dict): Dictionary containing xarray Datasets.
    Returns:     dict: Updated dictionary with averaged/selected data and a copy of the original with name _full appended.
    """
    #copy dictionary as all 3 dims before averaging depth
    param_dict_WholeYear10Layers = {key: dataset.copy(deep=True) for key, dataset in param_dict.items()}  # Create a true copy with original 10 layers

    for key in param_dict:
        dataset = param_dict[key]
        print(f"Processing key '{key}' with dataset:")
        print(dataset)
        print(f"\n")
        # Iterate over each variable in the dataset
        for var_name in dataset.data_vars:
            #  # Extract top layer _tp and add new _tp dataset
            top_layer_var_name = var_name.replace('_wc', '_tp')  # create new variable named for top layer 
            dataset[top_layer_var_name] = dataset[var_name][:, 0, :]  # select top layer (layer index 0) and create new  dataset
            # Extract bottom layer variable and add new  _bt
            bottom_layer_var_name = var_name.replace('_wc', '_bt')  # Create new variable name for bottom layer
            dataset[bottom_layer_var_name] = dataset[var_name][:, 9, :]  # Select bottom layer (layer index 9) and create new dataset
            # # Extract min value across middle layers (layers 1 to 8) _md
            # mid_layer_var_name1 = var_name.replace('_wc', '_md')
            # dataset[mid_layer_var_name1] = dataset[var_name][:, 1:9, :].min(dim='siglay')  # min value across layers 1-8, excludes top (0) and bottom (9)
            # # create Average across middle layers (layers 1 to 8) _md
            # mid_layer_var_name2 = var_name.replace('_wc', '_mA')
            # dataset[mid_layer_var_name2] = dataset[var_name][:, 1:9, :].mean(dim='siglay')  # Average across layers 1-8, excludes top (0) and bottom (9)

            # WC averaging
            # print(f"Copies made and renamed using original _wc with shape of variable '{var_name}':", dataset[var_name].dims, dataset[var_name].shape)
            # #Average value across all 10 WC (layers 0 to 9) ### Note _wA and mA represents a copy made with Averaged value not min and these are currently not used in box pot but are in excel/text summary
            # wc_layer_var_name1 = var_name.replace('_wc', '_wA')
            # dataset[wc_layer_var_name1] = dataset[var_name][:, 0:10, :].mean(dim='siglay')
            # # WC Maximum
            # print(f"Copies made and renamed using original _wc with shape of variable '{var_name}':", dataset[var_name].dims, dataset[var_name].shape)
            # #Max value across all 10 WC (layers 0 to 9) ### Note _wX represents a copy made with Max value not min and these are currently not used in box pot but are in excel/text summary
            # wc_layer_var_name1 = var_name.replace('_wc', '_wA')
            # dataset[wc_layer_var_name1] = dataset[var_name][:, 0:10, :].max(dim='siglay')
            # wc Minimum
             # Finally Extract min value across all 10WC (layers 0 to 9) and essentially replace _wc reducing dimensions
            wc_layer_var_name2 = var_name.replace('_wc', '_wc')
            dataset[wc_layer_var_name2] = dataset[var_name][:, 0:10, :].min(dim='siglay')
            print(f"Shape of variable '{var_name}' after _wc depth dimension removed on final extraction of min for _wc (min Vs _wA (Average)):", dataset[var_name].dims, dataset[var_name].shape, "\n")


        param_dict[key] = dataset  # Update the dictionary with the modified dataset

    return param_dict, param_dict_WholeYear10Layers

# Create a new Dataset with NaN values but keeping the same structure
def create_nan_dataset(original_dataset):
    new_dataset = original_dataset.copy(deep=True)  # Deep copy the original dataset to preserve structure and attributes
    for var in new_dataset.data_vars:  # Iterate over each data variable in the dataset
        new_dataset[var].values[:] = np.nan  # Set all values in the data variable to NaN
    return new_dataset  # Return the new dataset with NaN values

def calculate_mid_layer_depth_from_surface(ssm, total_depth, layer_number):
    """Calculate the midpoint depth for a given cell in meters from the surface.
    Parameters:
    total_depth (float): The total depth of the cell in meters.
    layer_number (int): The layer number (1 for surface, 10 for bottom).
    Returns:
    tuple: Cumulative fraction top, cumulative fraction bottom, and midpoint depth in meters from the surface (negative value).
    """
    depth_fraction = np.array(ssm['siglev_diff']) / 100
    if layer_number < 1 or layer_number > len(depth_fraction):
        raise ValueError("Layer number must be between 1 and 10.")

    # Calculate cumulative depth fraction up to the given layer
    cumulative_fraction_top = -np.sum(depth_fraction[:layer_number - 1]) * total_depth # Make depth negative , Note: [-1] as layer number (1-based) to an index (0-based), which matches the numpy array. e.g. layer 1 is index 0, layer 2 is index 1.
    cumulative_fraction_bottom = -np.sum(depth_fraction[:layer_number]) * total_depth # Make depth negative
    # Calculate the midpoint depth from the surface as a negative value
    mid_layer_depth_from_surface = (cumulative_fraction_top + cumulative_fraction_bottom) / 2
    # Round the output to two decimal places
    cumulative_fraction_top = round(cumulative_fraction_top, 2)
    cumulative_fraction_bottom = round(cumulative_fraction_bottom, 2)
    mid_layer_depth_from_surface = round(mid_layer_depth_from_surface, 2)
    
    return cumulative_fraction_top, cumulative_fraction_bottom, mid_layer_depth_from_surface

def main():
    ##############################
    #  Define input variables  ### change the model_var to needed eg temp etc
    # List of thresholds to iterate over
    DO_thresh = ["2"]
    scope = "wc"  ### modified now to just deterimine input data file as I then subsample the 10 layers of Water Column (wc)

    ################################
    # global variables , configuration, and data sources
    ssm, case = read_case('SSM_config_mi.yaml')

    #pull all global variables , dictionaries and datases from from SSM (yaml fle) and define
    shp = ssm['paths']['shapefile']#Get shapefile path    
    ###Here I am  relatively defining shp file location - see yaml and doing it relative. this includes new penn cove andother regions 
    processed_netcdf_script_output_dir = ssm['paths']['processed_output']  # SSM output files used as input to this directory
    script_output_dir = ssm['paths']['graphics']
        # Ensure the directory exists
    if not os.path.exists(script_output_dir):
        os.makedirs(script_output_dir)

    ###################
    # load shapefile and region node n used by the state
    # then pull regions names from shape file and parse to a list to use 
    print(f'\nShapefile to gdf preparation:')
    gdf = clean_shapefile_check16012_len(shp) #function call (in helper file) to: read shp, clean as problem with 16013, not 16012 rows, and check len and Nans
    gdf=gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby('Regions').count().index.to_list()  # 1)Group by the 'Regions' column, count the number of 'node_id' entries for each region,2) extract the index of the grouped DataFrame (which are the unique region names), and 3)convert this index to a list.
    regions.remove('Other') # These will be removed in future iterations

    MinParam_timeseries_DOX = load_nc(ssm, case, gdf, 'DOXG', 'min')
    MaxParam_timeseries_DOX = load_nc(ssm, case, gdf, 'DOXG', 'max')
    MeanParam_timeseries_DOX = load_nc(ssm, case, gdf, 'DOXG')

    [ndays,nlevels,nnodes]=MinParam_timeseries_DOX[next(iter(MinParam_timeseries_DOX))].dims # Get number of days and nodes

    MinParam_timeseries_temp = load_nc(ssm, case, gdf, 'temp', 'min')
    MaxParam_timeseries_temp = load_nc(ssm, case, gdf, 'temp', 'max')
    MeanParam_timeseries_temp = load_nc(ssm, case, gdf, 'temp')

    MinParam_timeseries_sal = load_nc(ssm, case, gdf, 'salinity', 'min')
    MaxParam_timeseries_sal = load_nc(ssm, case, gdf, 'salinity', 'max')
    MeanParam_timeseries_sal = load_nc(ssm, case, gdf, 'salinity')

    ## Transformation and exporting the centroid coordinates from shape file
    
    # Transform the GeoDataFrame to the final CRS
    gdf_transformed = gdf.to_crs('epsg:4326')

    # Calculate centroids from the transformed geometry
    gdf_transformed['calculated_centroid'] = gdf_transformed.geometry.centroid  # Calculate centroids in EPSG:4326
    gdf_transformed['calculated_lat'] = gdf_transformed['calculated_centroid'].y
    gdf_transformed['calculated_long'] = gdf_transformed['calculated_centroid'].x


    ## calcuated lat and long for comparision
    center_reprojected_lat = gdf_transformed['calculated_lat'].values
    center_reprojected_long = gdf_transformed['calculated_long'].values

    depth_m = (gdf['depth'].values) * 1000  # Change km to m

    # Coordinate arrays for each dimension
    coords = {
        "day": {  # Time-based coordinates
            "time": xr.DataArray(
                pd.date_range('2014-01-05', periods=361),  
                dims=("day",)
            )
        },
        "siglay": {  # Depth-based coordinates
            "depth_fraction": xr.DataArray(
                [3.2, 5.7, 7.5, 8.9, 10.1, 11.1, 12.1, 13.0, 13.8, 14.6],
                dims=("siglay",)
            )
        },
        "node": {  # Node-based coordinates, now supporting multiple values
            "node_id": xr.DataArray(range(16012), dims=("node",)),  # 0-based
            "node_id_OrigGis": xr.DataArray(range(1, 16013), dims=("node",)),  # 1-based indexing added
            #"latitude": xr.DataArray(center_lat, dims=("node",)),  # Debug - Added direct latitude (not currently used)
            #"longitude": xr.DataArray(center_long, dims=("node",)),  # Debug - Added direct longitude (not currently used)
            "latitude_reproj": xr.DataArray(center_reprojected_lat, dims=("node",)), #using calc from shapefile geometry  
            "longitude_reproj": xr.DataArray(center_reprojected_long, dims=("node",)), # using calc from shapefile geometry 
            "total_depth_m": xr.DataArray(depth_m, dims=("node",))  #  Added total depth
        }
    }

    # DOX
    MinParam_timeseries_DOX = process_and_add_coordinates(MinParam_timeseries_DOX, coords)
    MeanParam_timeseries_DOX = process_and_add_coordinates(MeanParam_timeseries_DOX, coords)
    MaxParam_timeseries_DOX = process_and_add_coordinates(MaxParam_timeseries_DOX, coords)
    # Temp
    MinParam_timeseries_temp = process_and_add_coordinates(MinParam_timeseries_temp, coords)
    MeanParam_timeseries_temp = process_and_add_coordinates(MeanParam_timeseries_temp, coords)
    MaxParam_timeseries_temp = process_and_add_coordinates(MaxParam_timeseries_temp, coords)
    # Salinity
    MinParam_timeseries_sal = process_and_add_coordinates(MinParam_timeseries_sal, coords)
    MeanParam_timeseries_sal = process_and_add_coordinates(MeanParam_timeseries_sal, coords)
    MaxParam_timeseries_sal = process_and_add_coordinates(MaxParam_timeseries_sal, coords)

    # DOX to MinParam_timeseries and review
    MinParam_timeseries_DOX, MinParam_WholeYear10Layers_timeseries_DOX = average_or_select_by_depth_dataset(MinParam_timeseries_DOX)
    review_dictionary(MinParam_timeseries_DOX)
    MeanParam_timeseries_DOX, MeanParam_WholeYear10Layers_timeseries_DOX = average_or_select_by_depth_dataset(MeanParam_timeseries_DOX)
    MaxParam_timeseries_DOX, MaxParam_WholeYear10Layers_timeseries_DOX = average_or_select_by_depth_dataset(MaxParam_timeseries_DOX)
    # temp:
    MinParam_timeseries_temp, MinParam_WholeYear10Layers_timeseries_temp = average_or_select_by_depth_dataset(MinParam_timeseries_temp)
    MeanParam_timeseries_temp, MeanParam_WholeYear10Layers_timeseries_temp = average_or_select_by_depth_dataset(MeanParam_timeseries_temp)
    MaxParam_timeseries_temp, MaxParam_WholeYear10Layers_timeseries_temp = average_or_select_by_depth_dataset(MaxParam_timeseries_temp)
    # sal:
    MinParam_timeseries_sal, MinParam_WholeYear10Layers_timeseries_sal = average_or_select_by_depth_dataset(MinParam_timeseries_sal)
    MeanParam_timeseries_sal, MeanParam_WholeYear10Layers_timeseries_sal = average_or_select_by_depth_dataset(MeanParam_timeseries_sal)
    MaxParam_timeseries_sal, MaxParam_WholeYear10Layers_timeseries_sal = average_or_select_by_depth_dataset(MaxParam_timeseries_sal)

    # Create a dictionary with new datasets having NaN values
    Calculated_WholeYear10Layers_3D_Xarray = {
        'wqm_reference': create_nan_dataset(MinParam_WholeYear10Layers_timeseries_DOX['wqm_reference']),  # Create NaN dataset for 'wqm_reference'
        'exist': create_nan_dataset(MinParam_WholeYear10Layers_timeseries_DOX['exist'])  # Create NaN dataset for 'exist'
    }

    # Rename the data variables in the new datasets
    for key in Calculated_WholeYear10Layers_3D_Xarray:
        Calculated_WholeYear10Layers_3D_Xarray[key] = Calculated_WholeYear10Layers_3D_Xarray[key].rename_vars({'DOXG_daily_min_wc': 'Newdata_param'})  # Rename 'DOXG_daily_min_wc'

    # Make new dictionary for geometry that is 2d 

    # Add an exact copy of 'NewDataset' called 'NewParam2' to each dataset
    for key in Calculated_WholeYear10Layers_3D_Xarray:
        Calculated_WholeYear10Layers_3D_Xarray[key]['NewParam_copy'] = Calculated_WholeYear10Layers_3D_Xarray[key]['Newdata_param'].copy(deep=True)  # Create a deep copy of 'NewDataset' and assign it to 'NewParam2'

    # Rename 'NewParam2' to 'NewParam2_renamed' in each dataset
    for key in Calculated_WholeYear10Layers_3D_Xarray:
        Calculated_WholeYear10Layers_3D_Xarray[key] = Calculated_WholeYear10Layers_3D_Xarray[key].rename_vars({'NewParam_copy': 'NewParam2'})  # Rename 'NewParam_copy' to 'NewParam2'

    # Create an exact copy of the Calculated_WholeYear10Layers_3D_Xarray dictionary and call it SSM_geometry_2D
    SSM_geometry_2D = {key: ds.copy(deep=True) for key, ds in Calculated_WholeYear10Layers_3D_Xarray.items()}

    #clean up 3d calculation xarray as no parameters needed - Delete the datasets so they are empty data arrays
    for key in Calculated_WholeYear10Layers_3D_Xarray:  # Iterate through each key
        dataset = Calculated_WholeYear10Layers_3D_Xarray[key]  # Access the dataset
        del dataset['Newdata_param']  # Delete Newdata_param
        del dataset['NewParam2']  # Delete NewParam2

    #drop the time dimensions amd add geometry data arrays to exist only 
    for key in SSM_geometry_2D:
        ds = SSM_geometry_2D[key]  # Extract dataset
        if 'day' in ds.dims:
            # Apply drop_dims only to data variables while keeping coordinates
            SSM_geometry_2D[key] = ds[[var for var in ds.data_vars]].drop_dims('day')

    # Remove 'wqm_reference' if it exists
    SSM_geometry_2D.pop('wqm_reference', None)

    # Loop through each remaining dataset and add NaN-filled variables
    for key in SSM_geometry_2D:
        ds = SSM_geometry_2D[key]  # Extract the dataset

        # Create NaN-filled DataArrays matching depth_fraction's shape
        nan_array = np.full(ds['depth_fraction'].shape, np.nan)

        # Assign NaN values to new variables
        ds = ds.assign({
            'cumulative_fraction_top': (('siglay',), nan_array),
            'cumulative_fraction_bottom': (('siglay',), nan_array),
            'mid_depth_from_surface': (('siglay',), nan_array),
        })

        # Save the modified dataset back
        SSM_geometry_2D[key] = ds

    # Loop through each dataset and update the DataArrays
    for key in SSM_geometry_2D:
        ds = SSM_geometry_2D[key]  # Extract the dataset

        # Get the node_id values for the dataset
        node_ids = ds.coords['node_id'].values

        # Create empty arrays for the new variables with the correct dimensions (10 layers per node_id)
        cumulative_fraction_top_values = np.full((len(node_ids), 10), np.nan)
        cumulative_fraction_bottom_values = np.full((len(node_ids), 10), np.nan)
        mid_depth_from_surface_values = np.full((len(node_ids), 10), np.nan)

        # Loop through all node_ids
        for idx, node_id in enumerate(node_ids):
            # Get the corresponding total depth for each node_id
            total_depth = SSM_geometry_2D['exist'].total_depth_m.isel(node=idx).values

            # Loop through the layers to calculate and store the values
            for layer_number in range(1, 11):  # Loop through layers 1 to 10
                cumulative_fraction_top, cumulative_fraction_bottom, mid_depth_from_surface = calculate_mid_layer_depth_from_surface(ssm, total_depth, layer_number)

                # Populate the arrays for each layer
                cumulative_fraction_top_values[idx, layer_number - 1] = cumulative_fraction_top
                cumulative_fraction_bottom_values[idx, layer_number - 1] = cumulative_fraction_bottom
                mid_depth_from_surface_values[idx, layer_number - 1] = mid_depth_from_surface

        # Assign the calculated values back to the dataset
        ds = ds.assign({
            'cumulative_fraction_top': (('node', 'siglay'), cumulative_fraction_top_values),
            'cumulative_fraction_bottom': (('node', 'siglay'), cumulative_fraction_bottom_values),
            'mid_depth_from_surface': (('node', 'siglay'), mid_depth_from_surface_values),
        })

        # Save the modified dataset back
        SSM_geometry_2D[key] = ds


    # Initialize an empty list to store the data
    qa_data = []

    # Loop through each node_id and calculate the total_depth and cumulative_fraction_bottom for layer 10 from 'exist'
    for idx, node_id in enumerate(SSM_geometry_2D['exist'].coords['node_id'].values):
        # Get the total depth for this node_id from 'exist' dataset
        total_depth = SSM_geometry_2D['exist'].total_depth_m.isel(node=idx).values

        # Get the cumulative_fraction_bottom for layer 10 from 'exist' and make it positive
        cumulative_fraction_bottom = SSM_geometry_2D['exist'].cumulative_fraction_bottom.isel(node=idx, siglay=9).values

        # Make cumulative_fraction_bottom positive to match the original
        cumulative_fraction_bottom = abs(cumulative_fraction_bottom)

        # Calculate the difference (should be 0 if the calculations are correct)
        difference = total_depth - cumulative_fraction_bottom

        # Append the result to the list
        qa_data.append([node_id, total_depth, cumulative_fraction_bottom, difference])

    # Create a pandas DataFrame to display the results
    qa_df = pd.DataFrame(qa_data, columns=['node_id', 'total_depth', 'cumulative_fraction_bottom', 'difference'])

    # Output file path
    output_file = os.path.join(script_output_dir, 'qa_comparison_depths.csv')

    # Save the DataFrame to the output directory as a CSV file
    qa_df.to_csv(output_file, index=False)

    # Display the DataFrame
    print(qa_df)

    plot_parameter_depth(qa_df['cumulative_fraction_bottom'].values, gdf, script_output_dir, 'Depth_m_calculated') #plot it
    # Clean up all variables
    del qa_data, qa_df, idx, node_id, total_depth, cumulative_fraction_bottom, difference, output_file

    # Call the function to export
    #shared inputs:
    output_dir = 'SSM_output/SSM_data_working'
    encoding = {'zlib': True, 'complevel': 4} #set 0 for no compression (few seconds) vs 4 reasonable (30sec) and 9 (took 1 min but abut same size as 4)

    # Call the function to export MinParam_timeseries, MaxParam_timeseries, and MeanParam_timeseries forall parameters
    #DOX
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MinParam_timeseries_DOX, dictionary_name="MinParam_timeseries_DOX", output_dir=output_dir, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MaxParam_timeseries_DOX, dictionary_name="MaxParam_timeseries_DOX", output_dir=output_dir, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MeanParam_timeseries_DOX, dictionary_name="MeanParam_timeseries_DOX", output_dir=output_dir, encoding=encoding)
    # temp:
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MeanParam_timeseries_temp, dictionary_name="MeanParam_timeseries_temp", output_dir=output_dir, encoding=encoding)
    # sal:
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MeanParam_timeseries_sal, dictionary_name="MeanParam_timeseries_sal", output_dir=output_dir, encoding=encoding)
    print(f"Functions complete for selected time series\n\n") #debug

    # Call the function to export the full 10 layer  NetCDF files
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MinParam_WholeYear10Layers_timeseries_DOX, dictionary_name="MinParam_WholeYear10Layers_timeseries_DOX", output_dir=output_dir, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MeanParam_WholeYear10Layers_timeseries_DOX, dictionary_name="MeanParam_WholeYear10Layers_timeseries_DOX", output_dir=output_dir, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MaxParam_WholeYear10Layers_timeseries_DOX, dictionary_name="MaxParam_WholeYear10Layers_timeseries_DOX", output_dir=output_dir, encoding=encoding)
    # temp:
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MeanParam_WholeYear10Layers_timeseries_temp, dictionary_name="MeanParam_WholeYear10Layers_timeseries_temp", output_dir=output_dir, encoding=encoding)
    # sal:
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MeanParam_WholeYear10Layers_timeseries_sal, dictionary_name="MeanParam_WholeYear10Layers_timeseries_sal", output_dir=output_dir, encoding=encoding)
    print(f"Functions complete for full 10 layer datasets\n\n")  # Debug

    ### Dictionaries used for geometry and templates
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=Calculated_WholeYear10Layers_3D_Xarray, dictionary_name="Calculated_WholeYear10Layers_3D_Xarray", output_dir=output_dir, encoding=encoding)
    export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=SSM_geometry_2D, dictionary_name="SSM_geometry_2D", output_dir=output_dir, encoding=encoding)

if __name__ == '__main__': main()
