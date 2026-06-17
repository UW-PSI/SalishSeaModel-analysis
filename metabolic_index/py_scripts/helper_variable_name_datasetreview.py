# 2025/07/15 updated- Stefano Mazzilli. 
# Functions called from main *.ipynb in this directory 
#
### Functions used for preparing variable names , checking data sets  etc
# ## general functions used to manipulate variable and text names in data and plots:

#import 
import xarray as xr

# Function to generate new variable names
def generate_new_name(original_name, suffix):
    parts = original_name.split('_')
    if len(parts) > 2:
        new_name = parts[0].capitalize() + '_' + parts[2].capitalize() + '_' + parts[-1].capitalize() + '_' + suffix
    else:
        new_name = '_'.join([part.capitalize() for part in parts]) + '_' + suffix
    return new_name
# Example call:
#original_name = 'temp_daily_min_wc'
#suffix = 'Aug'
#print(generate_new_name(original_name, suffix))  # Output: 'Temp_Min_Wc_Aug'


# Function to generate new variable names based on indices  - splits the input string by underscores, then joins the parts based on the provided indices. The indices are 1-based, so 1 corresponds to the first part, 2 to the second part, and so on
def Variable_naming(variable_name_input, *indices):
    parts = variable_name_input.split('_')
    new_name = '_'.join(parts[i-1] for i in indices)
    return new_name
# Example call:
# variable_name_input = 'Temp_Min_Wc_Aug'
# print(Variable_naming(variable_name_input, 1, 2))  # Output: 'Temp_Min'
# print(Variable_naming(variable_name_input, 1, 4))  # Output: 'Temp_Aug'
# print(Variable_naming(variable_name_input, 2, 3, 4))  # Output: 'Min_Wc_Aug'

### data dictionary manipulation
# # Function to check the contents of the dictionary with xarray datasets that can hold data arrays
def review_dictionary(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, xr.Dataset):
            dims = {dim: size for dim, size in value.sizes.items()}  # Use value.sizes to get dimensions and their sizes
            print(f"Dictionary with Key: {key} has the container Dataset (not directly a DataArray/variable in it) with dataarray: {list(value.data_vars)} and dimensions: {dims}")  # cointainer dataset with dataarrays listed and shape
        elif isinstance(value, xr.DataArray):
            dims = {dim: size for dim, size in zip(value.dims, value.shape)}  #  Get dimensions and their sizes
            print(f"Dictionary with Key: {key} directly has DataArray/variables (without the container Dataset) with shape: {value.shape} and dimensions: {dims}")  # dataarray direct shape
        else:
            print(f"Dictionary with Key: {key} is empty or contains an unexpected type: {type(value)}, not the container dataset or individual datasets")
# Example call: 
#review_dictionary(MinParam_timeseries)





##############################################################
###  Matrix preparation functions
#XYX THIS IS NOW UPDATED IN 1_do LOAD SO MOVE BACK HERE 
# # Function to add coordinates to datasets (2 part function ) NOTE 
# #       Set up with dummy data   see below 
# #       Draft code to automate for any dictionary is not working and commented out.
# #       Create a dictionary of coordinates  ### looks like this is fixed to "DOXG_daily_min_wc"
# # 
# # Import required libraries
# import xarray as xr
# import pandas as pd

# # Function: Add coordinates to datasets [currently applying this to each dataarray with a call loop as not functioing on higher level] - see ALSO BELOW "DOXG_daily_min_wc" ### as looks like itis hard coded
# def add_coordinates_to_dataset(dataset, coords):
#     """ Adds coordinates to a Dataset, with optional debug blocks for verification.
#     Args:
#         dataset (xarray.Dataset): The Dataset to add coordinates to.
#         coords (dict): A dictionary specifying coordinates for each dimension.
#     Returns:
#         xarray.Dataset: The Dataset with added coordinates.
#     """
#     # Debug: Before adding coordinates
#     print("\n# Debug: Before adding coordinates (in add_coordinates_to_dataset function)")
#     print("Dataset dimensions (before):", dataset.dims)
#     print("Dataset coordinates (before):")
#     print(dataset.coords)
    
#     # Adding coordinates
#     for dim, coord_values in coords.items():  # Iterate over dimensions in coords
#         if dim in dataset.dims:
#             print(f"# Debug: Adding coordinate for dimension '{dim}'")
#             dataset = dataset.assign_coords({dim: coord_values})
    
#     # Debug: After adding coordinates
#     print("\n# Debug: After adding coordinates(in add_coordinates_to_dataset function)")
#     print("Dataset dimensions (after):", dataset.dims)
#     print("Dataset coordinates (after):")
#     print(dataset.coords)
    
#     return dataset

# # Coordinate arrays to apply (DEPTH and Time not set yet, only nodes working)
# time_coords = xr.DataArray(
#     pd.date_range('2014-01-05', periods=361),  
#     dims=("dim_0",),
#     coords={"time": ("dim_0", pd.date_range('2014-01-05', periods=361))} # start date and number of time periods (days)
# )

# layer_coords = xr.DataArray(
#     [0, 10, 20, 30, 40, 50, 60, 70, 80, 90],  # Example depths
#     dims=("dim_1",),
#     coords={"depth": ("dim_1", range(10))}
# )

# node_coords = xr.DataArray(  ### zero  indexed coordinate system 0 , not uing 1 as start . needs node-1 to select correct
#     range(16012),  # # 16012 nodes starting from 0, ending 16011
#     dims=("dim_2",),
#     coords={"node_id": ("dim_2", range(16012))}
# )
# # node_coords = xr.DataArray(  ### 1 not 0 index- not using this
# #     range(1, 16013),  # creates a range of numbers from 1 to 16012; Start from 1 to align with tce values in the shape file (gdf)
# #     dims=("dim_2",),
# #     coords={"node_id": ("dim_2", range(1, 16013))}  # Assigns the node_id coordinate to the dim_2 dimension, using the same range of numbers from 1 to 16012
# # )


# # Create a dictionary of coordinates  ### looks like this is fixed to "DOXG_daily_min_wc"
# coords = {
#     "DOXG_daily_min_wc": {  # Variable name
#         "dim_0": time_coords,  # Time coordinate array
#         "dim_1": layer_coords,  # Layer coordinate array
#         "dim_2": node_coords   # Node coordinate array
#     }
# }

# def process_and_add_coordinates(dic_add_coordinates, coords):
#     """    Iterates through the dictionary of datasets and processes each variable to add coordinates.
#     Args:       Calls function def add_coordinates_to_dataset(dataset, coords):
#                 dic_add_coordinates (dict): Dictionary containing datasets to process.
#                 coords (dict): Dictionary specifying coordinates for each variable.
#     Returns:    dict: Updated dictionary with datasets containing added coordinates.
#     """
#     for key in dic_add_coordinates:
#         dataset = dic_add_coordinates[key]
#         print(f"Processing key '{key}' with dataset containing variables(in process_and_add_coordinates function): {list(dataset.data_vars)}\n")
        
#         # Iterate over each variable in the dataset
#         for var_name in dataset.data_vars:
#             print(f"Processing variable '{var_name}' in key '{key}'")
#             # First isolate only the variable by creating a new Dataset containing only the specified variable
#             var_dataset = xr.Dataset({var_name: dataset[var_name]})  # Create a new Dataset containing only the specified variable using xarray.Dataset, which constructs a new Dataset object from the provided dictionary. This isolates the variable for coordinate addition without affecting other variables
#             # Call function to add coordinates to the Dataset using dimension-specific coordinates
#             dataset_with_coords = add_coordinates_to_dataset(var_dataset, coords.get(var_name, {}))
            
#             print(f"\nDataset after adding coordinates for variable (in process_and_add_coordinates function)'{var_name}':")  # Debug output
#             print(dataset_with_coords)
          
#             # Replace the old dataset with the new version (with coordinates)
#             dic_add_coordinates[key][var_name] = dataset_with_coords[var_name]
    
#     return dic_add_coordinates
# # Example call 
# #MinParam_timeseries = process_and_add_coordinates(MinParam_timeseries, coords)

# # # Example: Iterate through dictionary eg. (MinParam_timeseries) and process each variable
# # dic_add_coordinates = MinParam_timeseries
# # for key in MinParam_timeseries:
# #     dataset = MinParam_timeseries[key]
# #     print(f"Processing key '{key}' with dataset containing variables: {list(dataset.data_vars)}\n")
    
# #     # Iterate over each variable in the dataset
# #     for var_name in dataset.data_vars:
# #         print(f"Processing variable '{var_name}' in key '{key}'")
# #         var_dataset = xr.Dataset({var_name: dataset[var_name]}) # First isolate only variable by Creating a new Dataset containing only the specified variable using xarray.Dataset, which constructs a new Dataset object from the provided dictionary. This isolates the variable for coordinate addition without affecting other variables
# #         dataset_with_coords = add_coordinates_to_dataset(var_dataset,coords.get(var_name, {}))  # Call function, add coordinates to the Dataset using dimension-specific coordinates
        
# #         print(f"\nDataset after adding coordinates for variable '{var_name}':")# Debug output
# #         print(dataset_with_coords)
      
# #         dic_add_coordinates[key][var_name] = dataset_with_coords[var_name]  # **Replace the old dataset with the new version (with coordinates)**


# # # Example call : Instead, simply iterate through dictionary and process each dataset rather than each data array indidually (this is not working for now)
# # for key in MinParam_timeseries:
# #     dataset = MinParam_timeseries[key]
# #     print(f"Processing key '{key}' with dataset containing variables: {list(dataset.data_vars)}\n")
# #     dataset_with_coords = add_coordinates_to_dataset(dataset, coords.get(key, {}))#Add coordinates to the entire dataset
# #     MinParam_timeseries[key] = dataset_with_coords# #Replace the old dataset with the new version (with coordinates)
# #     print(f"\nDataset after adding coordinates for key '{key}':")
# #     print(MinParam_timeseries[key])   # Debug output to verify

# #############################################################



#############################################################
### shapefile and geopandas manipulation:
#GDF load shapefile and remove exra line to make sure it is 16012  - then check length and nansimport geopandas as gpd
import geopandas as gpd
def clean_shapefile_check16012_len(input_shapefile):
    """Cleans a GeoDataFrame by removing an extra row, often found at the end, and checks for NaN values.

    Args:
        input_shapefile (str): Path to the input shapefile.

    Returns:
        geopandas.GeoDataFrame: Cleaned GeoDataFrame.
    """

    gdf = gpd.read_file(input_shapefile)  # Load the GeoDataFrame

    initial_rows = len(gdf)  # Check the initial number of rows
    print(f"Initial number of rows: {initial_rows}")
    print(f"Initial geodataframe loaded last rows:")
    #print(gdf.tail())  # Uncomment to print the last 5 rows to inspect -Debug

    if len(gdf) > 16012:  # Check if there are more than 16012 rows
        gdf = gdf.iloc[:-1]  # Remove the last row
        print("Removed an extra row as was 16013 not 16012 (check row 16013 was wrongly present in above shape file, and  see that did have zero values or nans for key colums).")
    elif len(gdf) < 16012:
        print("Error: The dataset has fewer than 16012 rows. Please check the input file using debug statements in function.")
        return None  # Exit if the dataset is too short

    final_rows = len(gdf)  # Check the final number of rows
    print(f"Final number of rows of the gdf that is returned: {final_rows}")

    nan_rows = gdf[gdf.isnull().any(axis=1)]  # Identify rows with at least one NaN value
    if not nan_rows.empty:
        print("Rows with NaN values(can be uncommented for debug display ):")
        #print(nan_rows)  # Print rows with NaN values  -Debug

    # Identify columns with NaN values in the identified rows
    nan_cols = nan_rows.columns[nan_rows.isnull().any()]
    print("Columns with NaN values in the identified rows:")
    print(nan_cols)
    return gdf
#eg call 
#clean_shapefile(input_shapefile) actual shapefile path
#gdf = clean_shapefile_check16012_len(shp)

### filter based on shapefile columns


############################################################################################################################3
### QA functions to subsample and to apply specific parameters across whole matrix used as inputs

def subsample_ssm_data(ssm_dictionary, subdirectories_to_subsample, specified_nodes):
    """
    Subsample SSM data to specific nodes for faster processing and testing.
    
    Parameters:
    - ssm_dictionary: Dictionary containing SSM data (e.g., SSMcalcs_dic)
    - subdirectories_to_subsample: List of subdirectory names to process
    - specified_nodes: List of node IDs to keep (1-based indexing)
    
    Returns:
    - Modified dictionary with same structure but subsampled data
    """
    
    print("="*80)  # Create 80-character separator line using string multiplication
    print("SUBSAMPLING SSM DATA TO SPECIFIC NODES")
    print("="*80)  # Create 80-character separator line using string multiplication
    
    # Convert to 0-based indexing for array operations
    nodes_0based = [node - 1 for node in specified_nodes]  # Subtract 1 from each node ID to convert from GIS 1-based to numpy 0-based indexing
    print(f"Subsampling to {len(specified_nodes)} nodes: {specified_nodes}")  # f-string formatting to show original 1-based node IDs
    print(f"(Using 0-based indices: {nodes_0based})")  # Show converted 0-based indices used for array operations
    
    # Process each specified subdirectory
    for subdirectory in subdirectories_to_subsample:  # Loop through list like ['CalMinParam_3D_pO2_insitu_kPa', 'CalMaxParam_3D_temp_daily_max_CT']
        if subdirectory in ssm_dictionary:  # Check if this subdirectory key exists in SSMcalcs_dic
            print(f"\nProcessing subdirectory: {subdirectory}")  # f-string formatting to insert variable value
            
            # Process each dataset within the subdirectory
            for dataset_key in ssm_dictionary[subdirectory].keys():  # .keys() returns list of dataset names like ['exist', 'wqm_reference']
                print(f"  Processing dataset: {dataset_key}")  # f-string formatting to insert dataset name
                
                # Get original dataset
                original_dataset = ssm_dictionary[subdirectory][dataset_key]  # Get the xarray Dataset object: SSMcalcs_dic[subdirectory][dataset_key]
                
                # Create new dataset with subsampled variables
                subsampled_vars = {}  # Initialize empty dictionary to store subsampled variables
                
                # Process each variable within the dataset
                for var_name in original_dataset.data_vars:  # .data_vars gives list of variable names in xarray Dataset
                    original_data = original_dataset[var_name]  # Get the xarray DataArray for this variable
                    original_shape = original_data.shape  # Get dimensions like (361, 10, 16012) from xarray DataArray
                    
                    # Subsample using dim_2 (nodes dimension) - known SSM structure
                    subsampled_data = original_data.isel(dim_2=nodes_0based)  # .isel() selects specific indices along dim_2 (nodes dimension)
                    
                    # Store in new variables dictionary
                    subsampled_vars[var_name] = subsampled_data  # Add subsampled DataArray to dictionary with same variable name
                    
                    print(f"    {var_name}: {original_shape} → {subsampled_data.shape}")  # Show shape change from subsampling
                
                # Create new dataset with subsampled variables and appropriate coordinates
                # Use coordinates from the first subsampled variable
                first_var = list(subsampled_vars.values())[0]  # Get first DataArray from subsampled variables dictionary
                subsampled_coords = first_var.coords  # Extract coordinates from first variable to use for new Dataset
                
                # Create new dataset
                new_dataset = xr.Dataset(subsampled_vars, coords=subsampled_coords)  # Create new xarray Dataset with subsampled variables and coordinates
                
                # Replace original dataset with subsampled dataset
                ssm_dictionary[subdirectory][dataset_key] = new_dataset  # Replace original Dataset with subsampled version in dictionary
                
                print(f"  Completed dataset: {dataset_key}")  # Confirmation message
        else:
            print(f"Subdirectory '{subdirectory}' not found in dictionary")  # Error message if subdirectory key doesn't exist
    
    print(f"\nSubsampling complete - dictionary structure preserved")  # Final confirmation message
    print(f"All following code will work with subsampled data")  # Note about impact on subsequent processing
    return ssm_dictionary  # Return the modified dictionary

def override_ssm_data_for_qa(ssm_dictionary, subdirectories_to_override, pO2_override_value=None, temp_override_value=None):
    """
    Override SSM data with specified test values for QA validation.
    
    Parameters:
    - ssm_dictionary: Dictionary containing SSM data (e.g., SSMcalcs_dic)
    - subdirectories_to_override: List of subdirectory names to process
    - pO2_override_value: Value to override all pO2 data (None = no override)
    - temp_override_value: Value to override all temperature data (None = no override)
    
    Returns:
    - Modified dictionary with same structure but overridden data (in-place modification)
    """
    
    print("="*80)  # Create 80-character separator line using string multiplication
    print("QA OVERRIDE: Setting custom values in SSM data for validation")
    print("="*80)  # Create 80-character separator line using string multiplication
    
    override_count = 0  # Counter to track how many data arrays were modified
    
    # Process each specified subdirectory (from subdirectories_to_subsample list defined earlier)
    for subdirectory in subdirectories_to_override:  # Loop through list like ['CalMinParam_3D_pO2_insitu_kPa', 'CalMaxParam_3D_temp_daily_max_CT']
        if subdirectory in ssm_dictionary:  # Check if this subdirectory key exists in SSMcalcs_dic
            print(f"\nProcessing subdirectory: {subdirectory}")  # f-string formatting to insert variable value
            
            # Process each dataset within the subdirectory (e.g., 'exist', 'wqm_reference')
            for dataset_key in ssm_dictionary[subdirectory].keys():  # .keys() returns list of dataset names in this subdirectory
                dataset = ssm_dictionary[subdirectory][dataset_key]  # Get the xarray Dataset object: SSMcalcs_dic[subdirectory][dataset_key]
                print(f"  Processing dataset: {dataset_key}")  # f-string formatting to insert dataset name
                
                # Override pO2 data if value provided (None check prevents override when not requested)
                if pO2_override_value is not None and 'pO2_insitu_kPa' in dataset.data_vars:  # Check if override requested AND variable exists in xarray Dataset
                    original_shape = dataset['pO2_insitu_kPa'].shape  # Get dimensions like (361, 10, 3) from xarray DataArray
                    dataset['pO2_insitu_kPa'] = dataset['pO2_insitu_kPa'] * 0 + pO2_override_value  # Multiply by 0 to clear, add override value to fill entire array
                    print(f"    pO2 set to {pO2_override_value:.3f} kPa for all {original_shape} data points")  # .3f formats float to 3 decimal places
                    override_count += 1  # Increment counter for tracking
                
                # Override temperature data if value provided (None check prevents override when not requested)  
                if temp_override_value is not None and 'temp_daily_max_CT' in dataset.data_vars:  # Check if override requested AND variable exists in xarray Dataset
                    original_shape = dataset['temp_daily_max_CT'].shape  # Get dimensions like (361, 10, 3) from xarray DataArray
                    dataset['temp_daily_max_CT'] = dataset['temp_daily_max_CT'] * 0 + temp_override_value  # Multiply by 0 to clear, add override value to fill entire array
                    print(f"    Temperature set to {temp_override_value}°C for all {original_shape} data points")  # .3f not needed for temp since it's typically integer
                    override_count += 1  # Increment counter for tracking
                    
        else:
            print(f"Subdirectory '{subdirectory}' not found in dictionary")  # Error message if subdirectory key doesn't exist
    
    print(f"\nQA Override complete - {override_count} data arrays modified")  # Report total number of arrays changed
    if pO2_override_value is not None:  # Only print if pO2 override was requested
        print(f"All pO2 data set to: {pO2_override_value:.3f} kPa")  # .3f formats float to 3 decimal places for readability
    if temp_override_value is not None:  # Only print if temperature override was requested
        print(f"All temperature data set to: {temp_override_value}°C")  # Temperature typically doesn't need decimal formatting
    
    return ssm_dictionary  # Return the modified dictionary (though changes are in-place)

# Example usage:
# 
# # Subsampling example:
# specified_nodes = [13789, 8841, 14409]  # Node IDs for testing (1-based indexing)
# subdirectories_to_subsample = ['CalMinParam_3D_pO2_insitu_kPa', 'CalMaxParam_3D_temp_daily_max_CT']
# SSMcalcs_dic = subsample_ssm_data(SSMcalcs_dic, subdirectories_to_subsample, specified_nodes)
#
# # QA override examples:
# # Test 1 QA validation:
# test_pO2_value = np.exp(betas[0])  # Calculate from regression coefficients
# test_temp_value = 15.0
# SSMcalcs_dic = override_ssm_data_for_qa(SSMcalcs_dic, subdirectories_to_subsample, 
#                                        pO2_override_value=test_pO2_value, 
#                                        temp_override_value=test_temp_value)
#
# # Custom test values:
# SSMcalcs_dic = override_ssm_data_for_qa(SSMcalcs_dic, subdirectories_to_subsample,
#                                        pO2_override_value=20.0, 
#                                        temp_override_value=12.0)
#
# # Only override temperature:
# SSMcalcs_dic = override_ssm_data_for_qa(SSMcalcs_dic, subdirectories_to_subsample,
#                                        temp_override_value=18.0)