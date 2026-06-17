# 2024/11/18 Stefano Mazzilli. 
# Functions called from main *.ipynb in this directory 
#
### Functions used for exports eg to excel and plots
# ## general functions used to manipulate variable and text names in data and plots:
import os
import subprocess

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib as mpl
import xarray as xr
import pandas as pd

def load_all_nc_datasets(output_dir, subdirectories_to_load):
    """
    Load all NetCDF datasets from specified subdirectories within a  given directory.

    Parameters:
    output_dir (str): Path to the output directory containing subdirectories with NetCDF files.
    subdirectories_to_load (list): A list of subdirectory names to load datasets from.

    Returns:
    dict: A dictionary of dictionaries containing xarray Datasets.
          The outer dictionary keys are the subdirectory names,
          and the inner dictionary keys are the NetCDF file names (without extension).
    """
    datasets = {}  # Initialize an empty dictionary to store the datasets

    # Iterate over each specified subdirectory
    for subdirectory in subdirectories_to_load:
        subdirectory_path = os.path.join(output_dir, subdirectory)  # Get the full path of the subdirectory
        if os.path.isdir(subdirectory_path):  # Check if it is a directory
            datasets[subdirectory] = {}  # Initialize a dictionary for the subdirectory

            # Iterate over each NetCDF file in the subdirectory
            for nc_file in os.listdir(subdirectory_path):
                if nc_file.endswith('.nc'):  # Check if the file is a NetCDF file
                    file_path = os.path.join(subdirectory_path, nc_file)  # Get the full path of the NetCDF file
                    dataset_name = os.path.splitext(nc_file)[0]  # Get the file name without extension
                    datasets[subdirectory][dataset_name] = xr.open_dataset(file_path)  # Load the dataset
        else:
            print(f"Directory not found: {subdirectory_path}")

    return datasets  # Return the dictionary of dictionaries containing the datasets

############################ Exports ######
## export arrays to excel for specific nodes with ANY no of days eg365 days of data: NOTE that 2_DO_sat now has updated version to replace this
# NOTE 

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

def export_xarray_to_excel(xarray_data, script_output_dir, file_export_name):
    """
    Exports an xarray DataArray to an Excel file in the specified output directory.

    Args:
        xarray_data: The xarray DataArray to export.
        script_output_dir: The directory path to save the Excel file.
        file_export_name: The name of the output Excel file.
    """

    # Filter out any non-existing times or invalid data (e.g., masked/NaNs)  
    if 'day' in xarray_data.dims:  # check if time dimension exists  
        valid_times = xarray_data['day'].values  # get all available time entries  
        xarray_data = xarray_data.sel(day=valid_times)  # safely select existing times only  

    # Convert xarray DataArray to Pandas DataFrame
    df = xarray_data.to_dataframe()

    # Reset the index to make the time dimension a regular column
    df = df.reset_index()

    # Check the dimensions and length of the DataFrame
    print("DataFrame dimensions to be exported:", df.shape)
    print("DataFrame columns to be exported:", df.columns)

    # Create the full file path
    full_filepath = os.path.join(script_output_dir, file_export_name)

    # Export the DataFrame to the specified Excel file
    df.to_excel(full_filepath, index=False)

    # Print a message indicating successful export
    print(f"Data exported to {full_filepath}")

# Example usage
#output_directory = script_output_dir  # Provided earlier
#export_filename = "FilteredRegion2_HardCoded_DOXG_daily_min_wc_Min.xlsx"  # 
#export_xarray_to_excel(filtered_region_2_data, output_directory, export_filename)  # 

# 
###################################################################################################
#Export function any dictionary of any dataset and datarray to directory and *.nc

def export_dictionary_of_nc_datasets(dictionary_of_nc_datasets, dictionary_name, output_dir, encoding):  
    """
    Export a dictionary of NetCDF datasets to a specified directory.
    Parameters:
    dictionary_of_nc_datasets (dict): Dictionary containing xarray Datasets.
    dictionary_name (str): Name of the dictionary to create a subdirectory.
    output_dir (str): Path to the output directory.
    encoding (dict): Encoding dictionary for NetCDF compression.

    This function creates a subdirectory with the given dictionary name in the specified output directory.
    It then iterates over each key in the dictionary and saves the corresponding dataset as a NetCDF file 
    in the subdirectory. Each dataset is saved with the key name as the file name.
    Structure:
    dictionary_of_nc_datasets  # dictionary level 1 (uses 'dictionary_of_nc_datasets' parameter, and will save to 'output_dir/dictionary_name')
    ├── key1  # dictionary level 2 (directory created with same name as 'key1')
    │   ├── <xarray.Dataset>  # dataset (saved as 'key1.nc' in the subdirectory)
    │   │   ├── var1  # data array
    │   │   ├── var2  # data array , etc...
    │   └── ...
    ├── key2  # dictionary level 2 (directory created with same name as 'key2')
    │   ├── <xarray.Dataset>  # dataset (saved as 'key2.nc' in the subdirectory)
    │   │   ├── var1  # data array
    │   │   ├── var2  # data array, etc... 
    │   └── ...
    ...
    etc.   
    """
    print(f'Starting on new dictionary')
    # Check if the dictionary is empty
    if not dictionary_of_nc_datasets:  # If the dictionary is empty
        print(f"No files to export for dictionary '{dictionary_name}', skipping to next dictionary.")
        return  # Exit the function

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)  # Create the output directory if it doesn't exist
    print(f"Output directory created or already exists: {output_dir}")
    
    # Create a subdirectory with the dictionary name
    subdirectory = os.path.join(output_dir, dictionary_name)  # Define the subdirectory path
    
    # Overwrite the subdirectory if it exists
    if os.path.exists(subdirectory):  # If the subdirectory exists
        print(f"Subdirectory '{subdirectory}' already exists and will be overwritten.")
    
    os.makedirs(subdirectory, exist_ok=True)  # Create the subdirectory if it doesn't exist
    print(f"Subdirectory created matching the dictionary name: {subdirectory}")

    # Iterate over each key in the dictionary_of_nc_datasets
    for key, dataset in dictionary_of_nc_datasets.items():  # Loop through each key and dataset in the dictionary
        # Define the file path for the NetCDF file
        file_path = os.path.join(subdirectory, f"{key}.nc")  # Define the file path for the NetCDF file
        
        # Delete the existing file if it exists 
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Existing file '{file_path}' deleted.")  
        
        print(f"Saving dataset for key '{key}' to file: {file_path}")
        
        if not isinstance(dataset, xr.Dataset): # Error check message if not xarray.Dataset
            print(f"[Error check] Key '{key}': Object is type {type(dataset)} — expected xarray.Dataset. This may cause an error.")  # CHANGED
            # If needed, convert with: dataset = dataset.to_dataset(name="your_var_name")  # but only if you're sure it's a DataArray

        # Save dataset using provided compression/encoding level
        dataset.to_netcdf(file_path, mode='w', encoding={var: encoding for var in dataset.data_vars})  # Save the dataset with the specified encoding #CHANGED
        print(f"Dataset for key '{key}' saved successfully\n")
    print(f"all datasets in this dictionary are complete\n\n")
# #example call:
# #shared inputs:
# output_dir = script_output_dir
# encoding = {'zlib': True, 'complevel': 4} #set 0 for no compression (few seconds) vs 4 reasonable (30sec) and 9 (took 1 min but abut same size as 4)
# #call:
# export_dictionary_of_nc_datasets(dictionary_of_nc_datasets=MinParam_timeseries_DOX, dictionary_name="MinParam_timeseries_DOX", output_dir=output_dir, encoding=encoding)  
############################################################################

#############################################################################
######## Plots  #############################################################

# Planar plot for depth data (must be positive and in m)

def plot_parameter_depth(parameter_data, gdf, output_path, variable_name):
    """
    Plots the given parameter data on a map and saves it as a PNG file.

    Parameters:
    parameter_data (array-like): The specific data array to be plotted.
    gdf (GeoDataFrame): The GeoDataFrame containing the spatial data.
    script_output_dir (str): Variable holding the string for the directory where the plot will be saved.
    variable_name (str): The name of the variable being plotted, used for labeling and file naming.
    """
   
    print(f"Length of parameter_data: {len(parameter_data)}")  # Debugging: Print length of parameter_data
    print(f"Length of gdf: {len(gdf)}")  # Debugging: Print length of gdf
    
    # Ensure the length matches
    if len(parameter_data) != len(gdf):
        print("Error: Length of data does not match the number of cells in gdf.")
        return
    
    # Add the data to the GeoDataFrame
    gdf.loc[:, variable_name] = parameter_data  # Use .loc to avoid SettingWithCopyWarning, by adding a new column with the name variable_name and assigning it the values from parameter_data

    # Filter rows where 'included_i' equals 1 (excludes masked shallow water values and those outside of WA)
    print(f"Number of rows in GeoDataFrame before filtering: {len(gdf)}")  # DEBUGGING: Before filter
    gdf = gdf[gdf['included_i'] == 1]  # Filter rows based on the column 'included_i'
    print(f"Number of rows in GeoDataFrame after filtering: {len(gdf)}")  # DEBUGGING: After filter
    # Check if any rows remain after filtering
    if gdf.empty:  # Handle case where no rows match the filter
        print("Warning: No rows found where 'included_i' equals 1. Plot will not be created.")
        return  # Exit the function to avoid plotting an empty dataset
    
    # Check the original CRS
    original_crs = gdf.crs
    print("Original CRS:", original_crs)
    # Transform CRS to EPSG:4326
    final_crs = 'epsg:4326'
    gdf = gdf.to_crs(final_crs)
    print("Transformed CRS:", final_crs)
    
    # Define the color scheme and boundaries using a dictionary
    color_boundaries = {
        0: 'red',
        10: 'orange',
        20: 'navajowhite',
        30: 'beige',
        40: 'skyblue',
        50: 'royalblue',
        100: 'midnightblue',
        200: 'darkblue'
    }

    # Extract boundaries and colors from the dictionary
    boundaries = list(color_boundaries.keys())  # Boundaries for color breaks
    colors = list(color_boundaries.values())  # Corresponding colors
    cmap = mpl.colors.ListedColormap(colors)  # Create colormap
    norm = mpl.colors.BoundaryNorm(boundaries, cmap.N, clip=True)  # Normalize to boundaries

    # Plot the data
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    plot = gdf.plot(column=variable_name, ax=ax, cmap=cmap, norm=norm)  # Apply colormap and normalization

    # Add background map with Stamen Terrain - not working
    # cx.add_basemap(ax, crs=gdf.crs.to_string(), source=cx.providers.Stamen.TerrainBackground)

    # Set titles and labels
    ax.set_title(f'{variable_name}', fontsize=14)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    
    # Set axis limits
    ax.set_xlim(-122.8, -122.1)  # Limiting longitude for Whidbey
    ax.set_ylim(47.9, 48.5)      # Limiting latitude for Whidbey
    # Uncomment the following lines to change the zoom level
    # ax.set_xlim(-123.5, -122)  # Limiting longitude for south sound
    # ax.set_ylim(47, 47.5)      # Limiting latitude for south sound 
    # ax.set_xlim(-125, -122)    # Limiting longitude for PSound
    # ax.set_ylim(47, 50)        # Limiting latitude for PSound
    
    # Create legend labels
    legend_labels = []
    for i in range(len(boundaries) - 1):
        legend_labels.append(f'{boundaries[i]} - {boundaries[i+1]}')
    legend_labels.append(f'{boundaries[-1]}+')
    # Create a legend
    handles = [mpl.patches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(colors))]
    # bbox_to_anchor=(0.05, 0.05, 0.3, 0.3) explanation e.g:
    # (0.05, 0.05): The lower-left corner of the legend box inside the plot
    # 0.3: The width of the legend box as a fraction of the plot width
    # 0.3: The height of the legend box as a fraction of the plot height
    ax.legend(handles=handles, title="Depth (m)", loc='lower left', fontsize=10, title_fontsize=12, bbox_to_anchor=(0.01, 0.01, 0.15, 0.3), bbox_transform=ax.transAxes)
    
    # Save the plot as a PNG file with the variable name
    output_file = f'{output_path}/{variable_name}_plot.png'
    plt.savefig(output_file, bbox_inches='tight')
    print(f'Plot saved as {output_file}')

# Example function call to plot depth (assuming depth_m and other variables are defined and are positive
#plot_parameter_depth(depth_m, gdf, script_output_dir, 'Depth_m')

########################################
# planar plot for DOXG data eg exist or ref NOT exist-ref
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib as mpl

def plot_parameter_DOXG(parameter_data, gdf, output_path, variable_name):
    """
    Plots the given parameter data on a map and saves it as a PNG file.

    Parameters:
    parameter_data (array-like): The specific data array to be plotted.
    gdf (GeoDataFrame): The GeoDataFrame containing the spatial data.
    script_output_dir (str): variable holding the string for the directory where the plot will be saved.
    variable_name (str): The name of the variable being plotted, used for labeling and file naming.
    """
   
    print(f"Length of parameter_data: {len(parameter_data)}")  # Debugging: Print length of parameter_data
    print(f"Length of gdf: {len(gdf)}")  # Debugging: Print length of gdf
    
    # Ensure the length matches
    if len(parameter_data) != len(gdf):
        print("Error: Length of data does not match the number of cells in gdf.")
        return
    
    # Add the data to the GeoDataFrame
    gdf.loc[:, variable_name] = parameter_data  #Use .loc to avoid SettingWithCopyWarning, by adding a new column with the name variable_name and assigning it the values from parameter_data

    # Filter rows where 'included_i' equals 1  (excludes masked shallow water values and those outside of WA)
    print(f"Number of rows in GeoDataFrame before filtering: {len(gdf)}")  # DEBUGGING: Before filter
    gdf = gdf[gdf['included_i'] == 1]  # Filter rows based on the column 'included_i'
    print(f"Number of rows in GeoDataFrame after filtering: {len(gdf)}")  # DEBUGGING: After filter
    # Check if any rows remain after filtering
    if gdf.empty:  # Handle case where no rows match the filter
        print("Warning: No rows found where 'included_i' equals 1. Plot will not be created.")
        return  # Exit the function to avoid plotting an empty dataset
    

    # Check the original CRS
    original_crs = gdf.crs
    print("Original CRS:", original_crs)
        # Transform CRS to EPSG:4326
    final_crs = 'epsg:4326'
    gdf = gdf.to_crs(final_crs)
    print("Transformed CRS:", final_crs)
    
    # Define the color scheme and boundaries using a dictionary
    color_boundaries = {
    0: 'red',
    2: 'orange',
    3: 'navajowhite',
    4: 'beige',
    5: 'skyblue',
    6: 'royalblue',
    7: 'midnightblue'
    }

    # Extract boundaries and colors from the dictionary
    boundaries = list(color_boundaries.keys())  # boundaries for color breaks
    colors = list(color_boundaries.values())  # corresponding colors
    cmap = mpl.colors.ListedColormap(colors)  # create colormap
    norm = mpl.colors.BoundaryNorm(boundaries, cmap.N, clip=True)  # normalize to boundaries

    # Plot the data
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    plot = gdf.plot(column=variable_name, ax=ax, cmap=cmap, norm=norm)  # apply colormap and normalization

    # Add background map with Stamen Terrain - not working
    #cx.add_basemap(ax, crs=gdf.crs.to_string(), source=cx.providers.Stamen.TerrainBackground)

    # Set titles and labels
    ax.set_title(f'{variable_name}', fontsize=14)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    
        # Set axis limits
    ax.set_xlim(-122.8, -122.1)  # Limiting longitude for Whidbey
    ax.set_ylim(47.9, 48.5)       # Limiting latitude for Whidbey
    # Uncomment the following lines to change the zoom level
    # ax.set_xlim(-123.5, -122)  # Limiting longitude for south sound
    # ax.set_ylim(47, 47.5)       # Limiting latitude for south sound 
    #ax.set_xlim(-125, -122)  # Limiting longitude for PSound
    #ax.set_ylim(47, 50)       # Limiting latitude for PSound
    
    
    
    # Create legend labels
    legend_labels = []
    for i in range(len(boundaries) - 1):
        legend_labels.append(f'{boundaries[i]} - {boundaries[i+1]}')
    legend_labels.append(f'{boundaries[-1]}+')
    # Create a legend
    handles = [mpl.patches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(colors))]
    # bbox_to_anchor=(0.05, 0.05, 0.3, 0.3) explanation e.g:
    # (0.05, 0.05): The lower-left corner of the legend box inside the plot
    # 0.3: The width of the legend box as a fraction of the plot width
    # 0.3: The height of the legend box as a fraction of the plot height
    ax.legend(handles=handles, title="DO mg/L", loc='lower left', fontsize=10, title_fontsize=12, bbox_to_anchor=(0.01, 0.01, 0.15, 0.3), bbox_transform=ax.transAxes)
    
    # Save the plot as a PNG file with the variable name
    output_file = f'{output_path}/{variable_name}_plot.png'
    plt.savefig(output_file, bbox_inches='tight')
    print(f'Plot saved as {output_file}')

# Eg. Function calls:exist min of water column
#parameter_data = MinParam_timeseries['wqm_baseline']['DOXG_daily_min_wc_Min']
#plot_parameter_DOXG(parameter_data, gdf, script_output_dir, 'Exist_DOXG_daily_min_wc_Min')


##############Planar plots existing minus ref

# planar plot for DOXG DIFFERerence data (exist -ref) not exist or ref which is range 10-0 mg/l
#1 ex-ref without rounding

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib as mpl

def plot_parameter_DOXG_dif(parameter_data, gdf, output_path, variable_name):
    """
    Plots the given parameter data on a map and saves it as a PNG file.

    Parameters:
    parameter_data (array-like): The specific data array to be plotted.
    gdf (GeoDataFrame): The GeoDataFrame containing the spatial data.
    script_output_dir (str): variable holding the string for the directory where the plot will be saved.
    variable_name (str): The name of the variable being plotted, used for labeling and file naming.
    """
   
    print(f"Length of parameter_data: {len(parameter_data)}")  # Debugging: Print length of parameter_data
    print(f"Length of gdf: {len(gdf)}")  # Debugging: Print length of gdf
    
    # Ensure the length matches
    if len(parameter_data) != len(gdf):
        print("Error: Length of data does not match the number of cells in gdf.")
        return
    
    # Add the data to the GeoDataFrame
    gdf.loc[:, variable_name] = parameter_data  #Use .loc to avoid SettingWithCopyWarning, by adding a new column with the name variable_name and assigning it the values from parameter_data

    # Filter rows where 'included_i' equals 1  (excludes masked shallow water values and those outside of WA)
    print(f"Number of rows in GeoDataFrame before filtering: {len(gdf)}")  # DEBUGGING: Before filter
    gdf = gdf[gdf['included_i'] == 1]  # Filter rows based on the column 'included_i'
    print(f"Number of rows in GeoDataFrame after filtering: {len(gdf)}")  # DEBUGGING: After filter
    # Check if any rows remain after filtering
    if gdf.empty:  # Handle case where no rows match the filter
        print("Warning: No rows found where 'included_i' equals 1. Plot will not be created.")
        return  # Exit the function to avoid plotting an empty dataset
    
    # Check the original CRS
    original_crs = gdf.crs
    print("Original CRS:", original_crs)
        # Transform CRS to EPSG:4326
    final_crs = 'epsg:4326'
    gdf = gdf.to_crs(final_crs)
    print("Transformed CRS:", final_crs)
    
    # Define the color scheme and boundaries using a dictionary where each value is assigned to a color bin:
    #     determined by the first key that is less than or equal to your data point. eg -0.3 would be in bin  for -0.75 
    #     as 0.75 is less than 0.3, However, the next boundary (-0.5), is greater so cant be that one

    color_boundaries = {
    -1: '#010101',#dark blue black
    -0.9: '#4d8684', #aqua blue
    -0.8: '#fcfc00', #yellow
    -0.7: '#f3be00', #light orange
    -0.6: '#e4760d', #dark orange
    -0.5: '#ae0100', #red
    -0.4: '#ef797b',#darker pink
    -0.3: '#f1cece' # pink hexadecimal code
    #-0.2: 'pink', # or use '#FF0000'  # red hexadecimal code
    #-0.1: 'blue', # or use '#FF0000'  # red hexadecimal code
    }

    # Extract boundaries and colors from the dictionary
    boundaries = list(color_boundaries.keys())  # boundaries for color breaks
    colors = list(color_boundaries.values())  # corresponding colors
    cmap = mpl.colors.ListedColormap(colors)  # create colormap
    norm = mpl.colors.BoundaryNorm(boundaries, cmap.N, clip=True)  # normalize to boundaries

    # Plot the data
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    plot = gdf.plot(column=variable_name, ax=ax, cmap=cmap, norm=norm)  # apply colormap and normalization

    # Add background map with Stamen Terrain - not working
    #cx.add_basemap(ax, crs=gdf.crs.to_string(), source=cx.providers.Stamen.TerrainBackground)

    # Set titles and labels
    ax.set_title(f'{variable_name}', fontsize=14)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    
        # Set axis limits
    #ax.set_xlim(-122.8, -122.1)  # Limiting longitude for Whidbey
    #ax.set_ylim(47.9, 48.5)       # Limiting latitude for Whidbey
    # Uncomment the following lines to change the zoom level
    #ax.set_xlim(-123.5, -122)  # Limiting longitude for south sound
    #ax.set_ylim(47, 47.5)       # Limiting latitude for south sound 
    ax.set_xlim(-123.3, -122.1)  # Limiting longitude for PSound
    ax.set_ylim(47, 48.4)       # Limiting latitude for PSound
    
    
    #### LEGEND COMMENTED OUT
    # # Create legend labels
    # legend_labels = []
    # for i in range(len(boundaries) - 1):
    #     legend_labels.append(f'{boundaries[i]} - {boundaries[i+1]}')
    # legend_labels.append(f'{boundaries[-1]}+')
    # # Create a legend
    # handles = [mpl.patches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(colors))]
    # # bbox_to_anchor=(0.05, 0.05, 0.3, 0.3) explanation e.g:
    # # (0.05, 0.05): The lower-left corner of the legend box inside the plot
    # # 0.3: The width of the legend box as a fraction of the plot width
    # # 0.3: The height of the legend box as a fraction of the plot height
    # ax.legend(handles=handles, title="DO mg/L", loc='lower left', fontsize=10, title_fontsize=12, bbox_to_anchor=(0.01, 0.01, 0.15, 0.3), bbox_transform=ax.transAxes)
    
    # Save the plot as a PNG file with the variable name
    output_file = f'{output_path}/{variable_name}_plot.png'
    plt.savefig(output_file, bbox_inches='tight')
    print(f'Plot saved as {output_file}')

# Eg. Function calls:exist min of water column
#parameter_data = MinParam_timeseries['wqm_baseline']['DOXG_daily_min_wc_Min']
#plot_parameter_DOXG_dif(parameter_data, gdf, script_output_dir, 'Exist_DOXG_daily_min_wc_Min')

############# BELOW IS DRAFT AND NOT USED
#2 ex-ref with rounding (excluding -0.25 same as RM code NOT SET UP YET) -REMOVE PLOT LABEL
# Create a boolean mask for values less than or equal to -0.25
#DO_diff_lt_0p25 = (DO_diff <= -0.25)
# Select rows from 'some_array' where the corresponding mask value is True
#selected_rows = some_array[DO_diff_lt_0p25]


import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib as mpl

def plot_parameter_DOXG_dif_round_25(parameter_data, gdf, output_path, variable_name):
    """
    Plots the given parameter data on a map and saves it as a PNG file.

    Parameters:
    parameter_data (array-like): The specific data array to be plotted.
    gdf (GeoDataFrame): The GeoDataFrame containing the spatial data.
    script_output_dir (str): variable holding the string for the directory where the plot will be saved.
    variable_name (str): The name of the variable being plotted, used for labeling and file naming.
    """
   
    print(f"Length of parameter_data: {len(parameter_data)}")  # Debugging: Print length of parameter_data
    print(f"Length of gdf: {len(gdf)}")  # Debugging: Print length of gdf
    
    # Ensure the length matches
    if len(parameter_data) != len(gdf):
        print("Error: Length of data does not match the number of cells in gdf.")
        return
    
    # Add the data to the GeoDataFrame
    gdf.loc[:, variable_name] = parameter_data  #Use .loc to avoid SettingWithCopyWarning, by adding a new column with the name variable_name and assigning it the values from parameter_data

    # Filter rows where 'included_i' equals 1  (excludes masked shallow water values and those outside of WA)
    print(f"Number of rows in GeoDataFrame before filtering: {len(gdf)}")  # DEBUGGING: Before filter
    gdf = gdf[gdf['included_i'] == 1]  # Filter rows based on the column 'included_i'
    print(f"Number of rows in GeoDataFrame after filtering: {len(gdf)}")  # DEBUGGING: After filter
    # Check if any rows remain after filtering
    if gdf.empty:  # Handle case where no rows match the filter
        print("Warning: No rows found where 'included_i' equals 1. Plot will not be created.")
        return  # Exit the function to avoid plotting an empty dataset
    
    # Check the original CRS
    original_crs = gdf.crs
    print("Original CRS:", original_crs)
        # Transform CRS to EPSG:4326
    final_crs = 'epsg:4326'
    gdf = gdf.to_crs(final_crs)
    print("Transformed CRS:", final_crs)
    
    # Define the color scheme and boundaries using a dictionary where each value is assigned to a color bin:
    #     determined by the first key that is less than or equal to your data point. eg -0.3 would be in bin  for -0.75 
    #     as 0.75 is less than 0.3, However, the next boundary (-0.5), is greater so cant be that one

    color_boundaries = {
    -1: '#010101',#dark blue black
    -0.9: '#4d8684', #aqua blue
    -0.8: '#fcfc00', #yellow
    -0.7: '#f3be00', #light orange
    -0.6: '#e4760d', #dark orange
    -0.5: '#ae0100', #red
    -0.4: '#ef797b',#darker pink
    -0.3: '#f1cece' # pink hexadecimal code
    #-0.2: 'pink', # or use '#FF0000'  # red hexadecimal code
    #-0.1: 'blue', # or use '#FF0000'  # red hexadecimal code
    }

    # Extract boundaries and colors from the dictionary
    boundaries = list(color_boundaries.keys())  # boundaries for color breaks
    colors = list(color_boundaries.values())  # corresponding colors
    cmap = mpl.colors.ListedColormap(colors)  # create colormap
    norm = mpl.colors.BoundaryNorm(boundaries, cmap.N, clip=True)  # normalize to boundaries

    # Plot the data
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    plot = gdf.plot(column=variable_name, ax=ax, cmap=cmap, norm=norm)  # apply colormap and normalization

    # Add background map with Stamen Terrain - not working
    #cx.add_basemap(ax, crs=gdf.crs.to_string(), source=cx.providers.Stamen.TerrainBackground)

    # Set titles and labels
    ax.set_title(f'{variable_name}', fontsize=14)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    
        # Set axis limits
    #ax.set_xlim(-122.8, -122.1)  # Limiting longitude for Whidbey
    #ax.set_ylim(47.9, 48.5)       # Limiting latitude for Whidbey
    # Uncomment the following lines to change the zoom level
    #ax.set_xlim(-123.5, -122)  # Limiting longitude for south sound
    #ax.set_ylim(47, 47.5)       # Limiting latitude for south sound 
    ax.set_xlim(-123.3, -122.1)  # Limiting longitude for PSound
    ax.set_ylim(47, 48.4)       # Limiting latitude for PSound
    
    
    
    # Create legend labels
    legend_labels = []
    for i in range(len(boundaries) - 1):
        legend_labels.append(f'{boundaries[i]} - {boundaries[i+1]}')
    legend_labels.append(f'{boundaries[-1]}+')
    # Create a legend
    handles = [mpl.patches.Patch(color=colors[i], label=legend_labels[i]) for i in range(len(colors))]
    # bbox_to_anchor=(0.05, 0.05, 0.3, 0.3) explanation e.g:
    # (0.05, 0.05): The lower-left corner of the legend box inside the plot
    # 0.3: The width of the legend box as a fraction of the plot width
    # 0.3: The height of the legend box as a fraction of the plot height
    ax.legend(handles=handles, title="DO mg/L", loc='lower left', fontsize=10, title_fontsize=12, bbox_to_anchor=(0.01, 0.01, 0.15, 0.3), bbox_transform=ax.transAxes)
    
    # Save the plot as a PNG file with the variable name
    output_file = f'{output_path}/{variable_name}_plot.png'
    plt.savefig(output_file, bbox_inches='tight')
    print(f'Plot saved as {output_file}')

# Eg. Function calls:exist min of water column
#parameter_data = MinParam_timeseries['wqm_baseline']['DOXG_daily_min_wc_Min']
#plot_parameter_DOXG_dif(parameter_data, gdf, script_output_dir, 'Exist_DOXG_daily_min_wc_Min')





#############################################################################################################

#########################Metabolic planar plots (png image and video files ##################################
# Call the function with the selected  planar plot bounds and selected dates using a copy of gdf
#       Note: nested and called within loop_each_time_interval_plot_parameter_metabolic_median() following 

import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
import contextily as cx

def plot_parameter_metabolic_median(parameter_data, gdf, output_path, plot_name, filename, xlim=None, ylim=None):
    """
    Plots the given parameter data on a map and saves it as a PNG file.

    Parameters:
    - parameter_data (array-like): The specific data array to be plotted (should match model grid size).
    - gdf (GeoDataFrame): The full GeoDataFrame containing spatial grid cells (full model domain, unfiltered).
    - output_path (str): Path to save output .png.
    - plot_name (str): Title used on the plot and as the new column in the GeoDataFrame.
    - filename (str): Output PNG filename (without extension).
    - xlim (tuple): Tuple specifying the x-axis limits (longitude).
    - ylim (tuple): Tuple specifying the y-axis limits (latitude).
    """
    
    # Debug: Print the shape of the parameter data for the selected date
    #print(f"[INFO] parameter_data_selected shape: {parameter_data.shape}")
    # Debug: Print the shape of the GeoDataFrame before filtering
    #print(f"[DEBUG] GeoDataFrame shape: {gdf.shape}")

    # Check if the length of the parameter data matches the length of gdf
    if len(parameter_data) != len(gdf):
        print(f"[ERROR] Length mismatch: parameter_data ({len(parameter_data)}) and gdf ({len(gdf)}) must be the same length.")
        return

    # Work on a copy of the GeoDataFrame to avoid modifying the original gdf
    gdf_plot = gdf.copy()  # Create a copy of the original GeoDataFrame

    # Add the parameter data as a new column to the copied GeoDataFrame
    gdf_plot[plot_name] = parameter_data.values  # Use .values to ensure it's a flat array

    # Filter the GeoDataFrame to include only rows where 'included_i' == 1 (exclude shallow/outside areas)
    # Debug: Print the number of rows in gdf before and after filtering for 'included_i' == 1
    #print(f"[DEBUG] Rows in gdf before filtering: {len(gdf_plot)}")
    gdf_plot = gdf_plot[gdf_plot['included_i'] == 1]
    #print(f"[DEBUG] Rows after filtering for 'included_i' == 1: {len(gdf_plot)}")

    # Coordinate system transformation - convert the GeoDataFrame to lat/lon (EPSG:4326)
    original_crs = gdf_plot.crs  # Print the original coordinate reference system
    #print(f"[DEBUG] Original CRS: {original_crs}")
    gdf_plot = gdf_plot.to_crs('EPSG:4326')  # Convert to WGS84 (lat/lon)
    #print(f"[DEBUG] Transformed CRS: {gdf_plot.crs}")

    # Define the color scheme using a dictionary: key = value range, value = color
    color_boundaries = {  
        0: 'red',        # Values < 1 will be colored red
        1: 'orange',     # Values ≥ 1 and < 2 will be orange
        2: 'skyblue',    # Values ≥ 2 will be skyblue
    }
    boundaries = [0, 1, 2, 200]  # Color boundaries specified = 3 intervals
    colors = ['red', 'orange', 'skyblue']   # = 3 intervals 
    
    cmap = mpl.colors.ListedColormap(colors)  # Create a colormap based on the specified colors
    norm = mpl.colors.BoundaryNorm(boundaries, len(colors), clip=True)  # Normalize values based on the number of bins/colors

    # Plotting the data with the specified colormap and normalization
    fig, ax = plt.subplots(1, 1, figsize=(19.2, 10.8))  # Create a new figure and set size to be divisible by 2 for video export and large
    #eg Width: 19.2 * 150dpi = 2880, and height: 10.8 * 150 = 1620 pixels -  dpi set below
    gdf_plot.plot(column=plot_name,ax=ax,cmap=cmap,norm=norm,edgecolor='gray', linewidth=0.4) #edge colour set to grey and increased to 0.5
    # Title and axis labels
    ax.set_title(plot_name, fontsize=14, ha='center')  # Set the title of the plot
    ax.set_xlabel('Longitude', fontsize=12)  # Set x-axis label
    ax.set_ylabel('Latitude', fontsize=12)   # Set y-axis label

    # Set plot bounds to the region of interest if provided
    if xlim:
        ax.set_xlim(xlim)  # Set x-axis limits
    if ylim:
        ax.set_ylim(ylim)  # Set y-axis limits

    # Creating a legend to explain the color coding of the data
    legend_labels = [
    f'< {boundaries[1]}',                # red: Values strictly less than 1
    f'{boundaries[1]}–{boundaries[2]}',  # orange: Values from 1 to 2
    f'{boundaries[2]}+'                  # skyblue: Values 2 and above
    ]

    # Create a color patch for each legend entry
    handles = [
    mpl.patches.Patch(color=colors[i], label=legend_labels[i]) 
    for i in range(len(colors))  # One handle per color bin
    ]

    # Add the legend to the plot, positioned to the right of the map #CHANGED- fixed legend positioning to avoid overlay
    ax.legend(
        handles=handles,
        title="Metabolic Index",
        loc='center left',  # Position outside the plot on the right
        fontsize=8,
        title_fontsize=10,
        bbox_to_anchor=(1.02, 0.5),  # Position to the right of the map area
        bbox_transform=ax.transAxes
    )

    # Add basemap background (terrain)
    try:
        # using: # CartoDB Positron (light-colored and grey water, minimalist map, no labels) - Source: CartoDB, OpenStreetMap, under the ODbL license
        cx.add_basemap(ax, crs=gdf_plot.crs, source=cx.providers.CartoDB.PositronNoLabels, alpha=1)  # 
        # alt:
        # cx.add_basemap(ax,
        #             crs=gdf_plot.crs,  # Ensure the CRS matches the gdf projection
        #             source=cx.providers.Esri.WorldShadedRelief,  # Esri World Shaded Relief (shaded terrain)
        #             alpha=1)
        #print(f"[INFO] Basemap added from Esri.WorldShadedRelief.")
                # cx.add_basemap(ax, crs=gdf_plot.crs, source=cx.providers.Esri.WorldPhysical, alpha=1)  # Physical terrain (natural tone)
    except Exception as e:
        print(f"[WARNING] Could not add basemap: {e}")

    # Save the plot as a PNG file with the given filename
    output_file = f'{output_path}/{filename}.png'  # Full path for the saved plot
    plt.savefig(output_file, bbox_inches='tight', dpi=200)  # Save the plot as a PNG, specifying resolution
    # plt.show()  # Uncomment for interactive use (display the plot)
    print(f"[INFO] Plot saved: {output_file}| Dimensions: {fig.get_size_inches()*fig.dpi}\n")  # Print the output filename
    plt.close()  # Close the plot to avoid memory issues during batch processing
    # Plotting the data with the specified colormap and normalization


##### OLD VERSION TO DELETE  of plotloop

# #### loop call nesting above planar plot functions to select dates and prepare outputs
# import pandas as pd
# import os


# def loop_each_time_interval_plot_parameter_metabolic_median(parameter_data, gdf, output_dir, plot_name_prefix, filename_prefix, xlim=None, ylim=None, start_date=None, end_date=None):
#     """
#     Loops through all available days in the parameter dataset and produces plots.

#     Parameters:
#     - parameter_data (xarray.DataArray): The specific data array to be plotted (should match model grid size).
#     - gdf (GeoDataFrame): The full GeoDataFrame containing spatial grid cells (full model domain, unfiltered).
#     - output_dir (str): Directory where plots will be saved.
#     - plot_name_prefix (str): Prefix for the plot title.
#     - filename_prefix (str): Prefix for the output PNG filename.
#     - xlim (tuple): Tuple specifying the x-axis limits (longitude).
#     - ylim (tuple): Tuple specifying the y-axis limits (latitude).
#     - start_date (str): Optional start date for the plots (format: 'YYYY-MM-DD').
#     - end_date (str): Optional end date for the plots (format: 'YYYY-MM-DD').
#     """
    
#     # Create the output directory if it does not exist
#     script_output_dir = os.path.join(output_dir, "planar_png_output")
#     os.makedirs(script_output_dir, exist_ok=True)

#     # Determine time bounds from the data array if not provided
#     if not start_date or not end_date:
#         start_date, end_date = str(parameter_data.coords['dim_0'].values[0]), str(parameter_data.coords['dim_0'].values[-1])
#         print(f'[INFO -loop call] Data array time coverage determined dynamically from dataset timeseries: Start = {start_date}, End = {end_date}\n')
#     else:
#         print(f'[INFO -loop call] Data array time coverage defined in input to function: Start = {start_date}, End = {end_date}\n')

#     #Prepare also a CSV export of all nodes before looping through days
#     all_data_df = pd.DataFrame() # Initialize an empty DataFrame to store the data to export to csv
#     node_id_OrigGis = parameter_data.coords['node_id_OrigGis'].values # Extract node_id_OrigGis for the first column
#     all_data_df['node_id_OrigGis'] = node_id_OrigGis #ie for full dataset shoudl be numbered 1 to 16012

#     # Loop through all available days in the parameter dataset and produce plots
#     for date in pd.date_range(start=start_date, end=end_date):
#         selected_date = pd.Timestamp(date)
#         parameter_data_selected = parameter_data.sel(dim_0=selected_date)  # Extract data for one day

#         # Skip if no data for the day
#         if parameter_data_selected.size == 0:
#             print(f"[WARNING -call] Skipping {selected_date.date()}: No data available for that which was selected.")
#             continue

#         # Prepare plot title and filename date information
#         selected_date_str = selected_date.strftime("%Y-%m-%d")  # Plot title
#         selected_date_filename = selected_date.strftime("%Y%m%d")  # Filename

#         # Debug: Check data shape for the selected date
#         print(f"[INFO -call] Plotting for selected: {selected_date_str} | Filename: {selected_date_filename} | Data shape input to call: {parameter_data_selected.shape}")

#         # Create a DataFrame for the selected date's data
#         date_df = pd.DataFrame(parameter_data_selected.values, columns=[selected_date_str])  #dataframe
#         all_data_df = pd.concat([all_data_df, date_df], axis=1) # Append the data to the all_data_df DataFrame

#         # Call the function with the selected plot bounds and selected dates using a copy of gdf
#         plot_name = f'{plot_name_prefix}\n{selected_date_str}'  # Across 2 lines
#         filename = f'{filename_prefix}{selected_date_filename}'
#         plot_parameter_metabolic_median(parameter_data_selected, gdf.copy(), script_output_dir, plot_name, filename, xlim=xlim, ylim=ylim)

#     # Save the DataFrame to a CSV file with the same filename_prefix
#     csv_filename = f'{filename_prefix}_all_dates.csv'  
#     all_data_df.to_csv(os.path.join(script_output_dir, csv_filename), index=False)  
#     print(f"[INFO -loop call] completed plot *.png export and data for each date also saved as a column in CSV in same directory (used for webgis): {os.path.join(script_output_dir, csv_filename)}")  

###################  Plot daily - this is existing OR ref version  
#note this calls the plot function for each day of data (above)
def loop_each_time_interval_plot_parameter_metabolic_median(parameter_data, gdf, output_dir, plot_name_prefix, filename_prefix, xlim=None, ylim=None, start_date=None, end_date=None):
    """
    Loops through all available days in the parameter dataset and produces:
    - PNG plots for each day (saved to disk)
    - Also exports a node-vs-date Excel file using a separate function
    
    Parameters:
    - parameter_data (xarray.DataArray): The specific data array to be plotted (should match model grid size)
    - gdf (GeoDataFrame): The full GeoDataFrame containing spatial grid cells (full model domain, unfiltered)
    - output_dir (str): Directory where plots will be saved
    - plot_name_prefix (str): Prefix for the plot title
    - filename_prefix (str): Prefix for the output PNG filename and Excel
    - xlim (tuple): Tuple specifying the x-axis limits (longitude)
    - ylim (tuple): Tuple specifying the y-axis limits (latitude)
    - start_date (str): Optional start date for the plots (format: 'YYYY-MM-DD')
    - end_date (str): Optional end date for the plots (format: 'YYYY-MM-DD')
    """
    
    # Create the output directory for PNG plots
    script_output_dir = os.path.join(output_dir, "planar_png_output")  # Subdirectory path
    os.makedirs(script_output_dir, exist_ok=True)  # Create if not already there

    # Determine time bounds from the data array if not provided
    if not start_date or not end_date:
        start_date = str(parameter_data.coords['dim_0'].values[0])  # First date available (index 0)
        end_date = str(parameter_data.coords['dim_0'].values[-1])  # Last date available (index -1)
        print(f'[INFO -loop call] Data array time coverage determined dynamically from dataset timeseries: Start = {start_date}, End = {end_date}\n')
    else:
        print(f'[INFO -loop call] Data array time coverage defined in input to function: Start = {start_date}, End = {end_date}\n')

    # Loop through all available days and generate plots
    for date in pd.date_range(start=start_date, end=end_date):  # Iterate through each date
        selected_date = pd.Timestamp(date)  # Convert to Timestamp format
        parameter_data_selected = parameter_data.sel(dim_0=selected_date)  # Select 1-day slice

        if parameter_data_selected.size == 0:
            print(f"[WARNING -call] Skipping {selected_date.date()}: No data available for selected day.")
            continue  # Skip to next day

        selected_date_str = selected_date.strftime("%Y-%m-%d")  # Date string for title
        selected_date_filename = selected_date.strftime("%Y%m%d")  # Date string for filename

        print(f"[INFO -call] Plotting for selected: {selected_date_str} | Filename: {selected_date_filename} | Data shape: {parameter_data_selected.shape}")

        # Build plot title and filename
        plot_name = f'{plot_name_prefix}\n{selected_date_str}'  # Two-line title
        filename = f'{filename_prefix}{selected_date_filename}'  # Final image filename

        # Nested call to - Generate the actual PNG using your plot function
        plot_parameter_metabolic_median(
            parameter_data_selected,
            gdf.copy(),  # Use copy to avoid modifying original GeoDataFrame
            script_output_dir,
            plot_name,
            filename,
            xlim=xlim,
            ylim=ylim
        )



#############################
### EXISTING - REFERENCE SPECIFIC
### function Metabolic median Existing - Reference planar plot call for each day of year plot *.png - later used for  yearly video *.mp4 
#put back later


### function Metabolic median Existing - Reference planar plot call for each day of year plot *.png - later used for  yearly video *.mp4 
## NOTE: this function is nested in function following: 
import matplotlib as mpl
import matplotlib.pyplot as plt
import contextily as cx
import pandas as pd
import numpy as np

def plot_parameter_metabolic_median_ExMinusRef(parameter_data, gdf, output_path, plot_name, filename, xlim=None, ylim=None):
    """
    Plots the given parameter data on a map and saves it as a PNG file.

    Parameters:
    - parameter_data (array-like): The specific data array to be plotted (should match model grid size).
    - gdf (GeoDataFrame): The full GeoDataFrame containing spatial grid cells (full model domain, unfiltered).
    - output_path (str): Path to save output .png.
    - plot_name (str): Title used on the plot and as the new column in the GeoDataFrame.
    - filename (str): Output PNG filename (without extension).
    - xlim (tuple): Tuple specifying the x-axis limits (longitude).
    - ylim (tuple): Tuple specifying the y-axis limits (latitude).
    """
    
    # Check if the length of the parameter data matches the length of gdf
    if len(parameter_data) != len(gdf):
        print(f"[ERROR] Length mismatch: parameter_data ({len(parameter_data)}) and gdf ({len(gdf)}) must be the same length.")
        return

    # Work on a copy of the GeoDataFrame to avoid modifying the original gdf
    gdf_plot = gdf.copy()  # Create a copy of the original GeoDataFrame

    # Add the parameter data as a new column to the copied GeoDataFrame
    gdf_plot[plot_name] = parameter_data.values  # Use .values to ensure it's a flat array

    # Filter the GeoDataFrame to include only rows where 'included_i' == 1 (exclude shallow/outside areas)
    gdf_plot = gdf_plot[gdf_plot['included_i'] == 1]

    # Coordinate system transformation - convert the GeoDataFrame to lat/lon (EPSG:4326)
    gdf_plot = gdf_plot.to_crs('EPSG:4326')  # Convert to WGS84 (lat/lon)



# `BoundaryNorm` applies colors to values in intervals like: [bin_edge[i], bin_edge[i+1])
# By adding `np.inf` as the last boundary, we ensure that values >= -0.1 (including positive differences)
# are correctly assigned to the last color bin.
#
# With clip=True:
# - Any value < -1 will be shown using the first color bin (darkest)
# - Any value >= -0.1 will be shown using the last color bin (lightest)


    # Define the color scheme using a dictionary: key = value range, value = color
    color_boundaries = {
        -np.inf: '#010101',  # black — values less than -1
        -1.0:    '#4d8684',  # dark aqua blue — -1.0 to -0.9
        -0.9:    '#fcfc00',  # yellow — -0.9 to -0.8
        -0.8:    '#f3be00',  # light orange — -0.8 to -0.7
        -0.7:    '#e4760d',  # dark orange — -0.7 to -0.6
        -0.6:    '#8B0000',  # dark red — -0.6 to -0.5
        -0.5:    '#ae0100',  # red — -0.5 to -0.4
        -0.4:    '#FF6347',  # light red — -0.4 to -0.3
        -0.3:    '#ef797b',  # darker pink — -0.3 to -0.2
        -0.2:    '#f1cece',  # pink — -0.2 to -0.1
        -0.1:    '#fce4ec'   # light pink — -0.1 and above
    }

    # Extract keys and add an upper bound to include values >= -0.1 (including positive numbers)
        # skip the first boundary key (-np.inf) because it's used to handle "less than the lowest bin"
        # and BoundaryNorm expects actual bin edges, not starting with -inf directly.
        # take from the second key onward using [1:], and then add np.inf to cover the top end.
    boundaries = list(color_boundaries.keys())[1:] + [np.inf]  # bin edges for BoundaryNorm (e.g., -1.0, -0.9, ..., -0.1, inf)

    # This gives us a list of color hex codes in order that matches the bins defined above
    colors = list(color_boundaries.values())  # colors for each bin

    # Create a matplotlib colormap from the list of colors
    cmap = mpl.colors.ListedColormap(colors)

    # Create a normalizer that maps data values to bins using the `boundaries` we defined
    # `clip=True` ensures that values outside the range are clipped to the nearest bin
    norm = mpl.colors.BoundaryNorm(boundaries, cmap.N, clip=True) 

    # Plotting the data with the specified colormap and normalization
    fig, ax = plt.subplots(1, 1, figsize=(19.2, 10.8))  # Create a new figure and set size
    gdf_plot.plot(column=plot_name, ax=ax, cmap=cmap, norm=norm, edgecolor='gray', linewidth=0.4)

    # Title and axis labels
    ax.set_title(plot_name, fontsize=14, ha='center')  # Set the title of the plot
    ax.set_xlabel('Longitude', fontsize=12)  # Set x-axis label
    ax.set_ylabel('Latitude', fontsize=12)  # Set y-axis label

    # Set plot bounds to the region of interest if provided
    if xlim:
        ax.set_xlim(xlim)  # Set x-axis limits
    if ylim:
        ax.set_ylim(ylim)  # Set y-axis limits

    # Creating a legend to explain the color coding of the data
    # Each bin covers: [lower bound, upper bound), except the last which covers everything >= -0.1
    legend_labels = [
        f'< {boundaries[0]}',                 # black: values < -1
        f'{boundaries[0]}–{boundaries[1]}',   # dark aqua blue: -1.0 to -0.9
        f'{boundaries[1]}–{boundaries[2]}',   # yellow: -0.9 to -0.8
        f'{boundaries[2]}–{boundaries[3]}',   # light orange: -0.8 to -0.7
        f'{boundaries[3]}–{boundaries[4]}',   # dark orange: -0.7 to -0.6
        f'{boundaries[4]}–{boundaries[5]}',   # dark red: -0.6 to -0.5
        f'{boundaries[5]}–{boundaries[6]}',   # red: -0.5 to -0.4
        f'{boundaries[6]}–{boundaries[7]}',   # light red: -0.4 to -0.3
        f'{boundaries[7]}–{boundaries[8]}',   # darker pink: -0.3 to -0.2
        f'{boundaries[8]}–{boundaries[9]}',   # pink: -0.2 to -0.1
        f'≥ {boundaries[9]}'                  # light pink: -0.1 and above
    ]



    # Create a color patch for each legend entry
    handles = [
        mpl.patches.Patch(color=colors[i], label=legend_labels[i])
        for i in range(len(colors))  # One handle per color bin
    ]

    # Add the legend to the plot, positioned to the right of the map #CHANGED- fixed legend positioning to avoid overlay
    ax.legend(
        handles=handles,
        title="Metabolic Index",
        loc='center left',  # Position outside the plot on the right
        fontsize=8,
        title_fontsize=10,
        bbox_to_anchor=(1.02, 0.5),  # Position to the right of the map area
        bbox_transform=ax.transAxes
    )

    # Add basemap background
    try:
        cx.add_basemap(ax, crs=gdf_plot.crs, source=cx.providers.CartoDB.PositronNoLabels, alpha=1)
    except Exception as e:
        print(f"[WARNING] Could not add basemap: {e}")

    # Save the plot as a PNG file with the given filename
    output_file = f'{output_path}/{filename}.png'  # Full path for the saved plot
    plt.savefig(output_file, bbox_inches='tight', dpi=200)  # Save the plot as a PNG, specifying resolution
    print(f"[INFO] Plot saved: {output_file}| Dimensions: {fig.get_size_inches()*fig.dpi}\n")  # Print the output filename
    plt.close()

########################

###################  Plot daily - this is existing - ref version  
#note this calls the plot function for each day of data (above)
def loop_each_time_interval_plot_parameter_metabolic_median_ExMinusRef(parameter_data, gdf, output_dir, plot_name_prefix, filename_prefix, xlim=None, ylim=None, start_date=None, end_date=None):
    """
    Loops through all available days in the parameter dataset and produces:
    - PNG plots for each day (saved to disk)
    - Also exports a node-vs-date Excel file using a separate function
    
    Parameters:
    - parameter_data (xarray.DataArray): The specific data array to be plotted (should match model grid size)
    - gdf (GeoDataFrame): The full GeoDataFrame containing spatial grid cells (full model domain, unfiltered)
    - output_dir (str): Directory where plots will be saved
    - plot_name_prefix (str): Prefix for the plot title
    - filename_prefix (str): Prefix for the output PNG filename and Excel
    - xlim (tuple): Tuple specifying the x-axis limits (longitude)
    - ylim (tuple): Tuple specifying the y-axis limits (latitude)
    - start_date (str): Optional start date for the plots (format: 'YYYY-MM-DD')
    - end_date (str): Optional end date for the plots (format: 'YYYY-MM-DD')
    """
    
    # Create the output directory for PNG plots
    script_output_dir = os.path.join(output_dir, "planar_png_output")  # Subdirectory path
    os.makedirs(script_output_dir, exist_ok=True)  # Create if not already there

    # Determine time bounds from the data array if not provided
    if not start_date or not end_date:
        start_date = str(parameter_data.coords['dim_0'].values[0])  # First date available (index 0)
        end_date = str(parameter_data.coords['dim_0'].values[-1])  # Last date available (index -1)
        print(f'[INFO -loop call] Data array time coverage determined dynamically from dataset timeseries: Start = {start_date}, End = {end_date}\n')
    else:
        print(f'[INFO -loop call] Data array time coverage defined in input to function: Start = {start_date}, End = {end_date}\n')

    # Loop through all available days and generate plots
    for date in pd.date_range(start=start_date, end=end_date):  # Iterate through each date
        selected_date = pd.Timestamp(date)  # Convert to Timestamp format
        parameter_data_selected = parameter_data.sel(dim_0=selected_date)  # Select 1-day slice

        if parameter_data_selected.size == 0:
            print(f"[WARNING -call] Skipping {selected_date.date()}: No data available for selected day.")
            continue  # Skip to next day

        selected_date_str = selected_date.strftime("%Y-%m-%d")  # Date string for title
        selected_date_filename = selected_date.strftime("%Y%m%d")  # Date string for filename

        print(f"[INFO -call] Plotting for selected: {selected_date_str} | Filename: {selected_date_filename} | Data shape: {parameter_data_selected.shape}")

        # Build plot title and filename
        plot_name = f'{plot_name_prefix}\n{selected_date_str}'  # Two-line title
        filename = f'{filename_prefix}{selected_date_filename}'  # Final image filename

        # Nested call to - Generate the actual PNG using your plot function
        plot_parameter_metabolic_median_ExMinusRef(
            parameter_data_selected,
            gdf.copy(),  # Use copy to avoid modifying original GeoDataFrame
            script_output_dir,
            plot_name,
            filename,
            xlim=xlim,
            ylim=ylim
        )

##############################################################################
#### excel outputs of planar data: 

# Builds a long-format DataFrame and excel ouput from node and time coordinates in a dataarray (3 column output)

def build_node_many_rows_vs_single_date_column_dataframe(parameter_data, output_dir, filename_prefix, start_date=None, end_date=None):
    """
    Builds a long-format DataFrame where:
    - Each row corresponds to a unique (node, date) pair
    - Columns are: node_id_OrigGis, date, value (parameter)
    Then saves the DataFrame to Excel with an extra 'readme' sheet.

    Parameters:
    - parameter_data (xarray.DataArray): 2D array with time and node dimensions (e.g., shape: time x node)
    - output_dir (str): Base directory to create the output folder for Excel
    - filename_prefix (str): Prefix for the saved Excel filename
    - start_date (str): Optional start date to limit timeseries (format: 'YYYY-MM-DD')
    - end_date (str): Optional end date to limit timeseries (format: 'YYYY-MM-DD')
    """

    # Determine time bounds from the data array if not provided
    if not start_date or not end_date:
        start_date = str(parameter_data.coords['dim_0'].values[0])  # Get first time entry in array
        end_date = str(parameter_data.coords['dim_0'].values[-1])   # Get last time entry in array
        print(f'[INFO - long format export] Date range auto-selected from dataset: {start_date} to {end_date}')
    else:
        print(f'[INFO - long format export] Date range defined in input: {start_date} to {end_date}')

    # Create output directory if needed
    script_output_dir = os.path.join(output_dir, "planar_png_output")  # Define subfolder path
    os.makedirs(script_output_dir, exist_ok=True)  # Create folder if doesn't already exist

    # Extract node ID array once for all dates
    node_ids = parameter_data.coords['node_id_OrigGis'].values  # Node ID values (e.g., 1 to 16012)

    all_rows = []  # List to collect each day's data as a separate DataFrame

    # Loop over all dates in the specified range
    for date in pd.date_range(start=start_date, end=end_date):  # Generate daily timestamps
        date_str = date.strftime('%Y-%m-%d')  # Format date for column value
        daily_data = parameter_data.sel(dim_0=date)  # Slice the parameter data for the specific date

        if daily_data.size == 0:  # Skip days with no data (masked or missing)
            print(f"[WARNING - export] Skipping {date.date()}: No data available.")
            continue

        # Build a DataFrame for this day's data with 3 columns: node, date, value
        df = pd.DataFrame({
            "node_id_OrigGis": node_ids,  # Copy node ID column
            "date": date_str,             # Set date value (same for all rows)
            "data": daily_data.values     # Flattened values for the selected date
        })

        all_rows.append(df)  # Append to list of all daily frames

    # Combine all daily DataFrames vertically into one long-format DataFrame
    final_df = pd.concat(all_rows, ignore_index=True)  # Reset index for clean Excel export

    # Save to Excel with 2 sheets: 'data' and 'readme'
    excel_path = os.path.join(script_output_dir, f"{filename_prefix}_ArcGIS_timeseries_ready.xlsx")  # Final Excel output path
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:  # Use context manager for Excel
        final_df.to_excel(writer, index=False, sheet_name='data')  # Export long-format data to sheet
        pd.DataFrame({"readme": [
            "This Excel file contains a long-format export.",
            "Each row represents one node on one date.",
            "Columns: node_id_OrigGis, date, data (parameter value)."
        ]}).to_excel(writer, index=False, sheet_name='readme')  # Add documentation tab

    print(f"[INFO - long format export] Excel saved with long-format data + readme: {excel_path}")

#########################
# NOTE: # USING this above 3 column version  instead for gis time series - this version below makes excel output with multi-column dates, one column for each date

#dataarray with date and 'node_id_OrigGis coords > excel with row for each node_id and (unique) and column for each dates entry (eg 365 columns)

def build_node_vs_date_dataframe(parameter_data, output_dir, filename_prefix, start_date=None, end_date=None):
    """
    Builds a DataFrame where:
    - Each row corresponds to a spatial node (from node_id_OrigGis),
    - Each column corresponds to a date,
    Then saves the DataFrame to Excel with an extra 'readme' sheet.
    
    Parameters:
    - parameter_data (xarray.DataArray): 2D array with time and node dimensions (e.g., shape: time x node)
    - output_dir (str): Base directory to create the output folder for Excel
    - filename_prefix (str): Prefix for the saved Excel filename
    - start_date (str): Optional start date to limit timeseries (format: 'YYYY-MM-DD')
    - end_date (str): Optional end date to limit timeseries (format: 'YYYY-MM-DD')
    
    This function works for any number of nodes or dates.
    """
    
    # Determine time bounds from the data array if not provided
    if not start_date or not end_date:
        start_date = str(parameter_data.coords['dim_0'].values[0])  # Take first available date in dataset (index 0)
        end_date = str(parameter_data.coords['dim_0'].values[-1])   # Take last available date in dataset (index -1 for last element)
        print(f'[INFO - dataframe export] Data array time coverage determined dynamically from dataset timeseries: Start = {start_date}, End = {end_date}\n')
    else:
        print(f'[INFO - dataframe export] Data array time coverage defined in input to function: Start = {start_date}, End = {end_date}\n')

    # Create output directory if needed
    script_output_dir = os.path.join(output_dir, "planar_png_output")  # Define subdirectory path
    os.makedirs(script_output_dir, exist_ok=True)  # Create folder if it doesn't already exist

    # Extract original node IDs from coordinate metadata
    node_id_OrigGis = parameter_data.coords['node_id_OrigGis'].values  # Node ID array, e.g., 1 to 16012
    all_data_df = pd.DataFrame({'node_id_OrigGis': node_id_OrigGis})  # Create base DataFrame with node ID column

    # Loop over date range and extract 1-day slices
    for date in pd.date_range(start=start_date, end=end_date):  # Create list of daily timestamps from start to end
        selected_date = pd.Timestamp(date)  # Convert to pandas Timestamp for consistency
        selected_date_str = selected_date.strftime("%Y-%m-%d")  # Format for column name

        # Select data for this day
        parameter_data_selected = parameter_data.sel(dim_0=selected_date)  # Use .sel to slice along time dimension

        # Skip if the selected slice has no data (e.g., masked)
        if parameter_data_selected.size == 0:
            print(f"[WARNING - export] Skipping {selected_date.date()}: No data available.")
            continue

        # Convert 1D data array to DataFrame with a single column named by date
        date_df = pd.DataFrame(parameter_data_selected.values, columns=[selected_date_str])  # Create column for one date

        # Concatenate column to the growing DataFrame — axis=1 means side-by-side
        all_data_df = pd.concat([all_data_df, date_df], axis=1)  # Merge on rows (nodes), new column for each day

    # Save to Excel with 2 sheets: 'data' and 'readme'
    excel_path = os.path.join(script_output_dir, f"{filename_prefix}_all_dates.xlsx")  # Final Excel file path
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:  # Use context manager for Excel output
        all_data_df.to_excel(writer, index=False, sheet_name='data')  # Export main node-date matrix
        pd.DataFrame({"readme": ["Each day of data for each node is tabulated in corresponding column"]}).to_excel(writer, index=False, sheet_name='readme')  # Add documentation tab

    print(f"[INFO - dataframe export] Excel saved with data + readme: {excel_path}")

###########################################  Make video from planar plots created in folder 

def create_video_from_png(video_location_dir, filename_prefix):
    # Save the current working directory
    original_directory = os.getcwd()
    
    # Change to the specified directory
    os.chdir(video_location_dir)
    
    ## Calls to make video
    print(f"Spawning of subprocess for ffmpeg command to produce video starting:\n")
    
    # Define the ffmpeg command using the filename prefix
    ffmpeg_command = (
        f"ffmpeg -y -framerate 6 -pattern_type glob -i '{filename_prefix}*.png' "
        f"-vf \"scale=trunc(iw/2)*2:trunc(ih/2)*2\" -c:v libx264 -r 30 -pix_fmt yuv420p {filename_prefix}_video.mp4"
    )
    subprocess.run(ffmpeg_command, shell=True) # Spawn process
    
    ## Calls complete close out
    os.chdir(original_directory) # Change back to the original directory
    print(f"\nChanged back to current working directory where scripts are: {os.getcwd()}")
    print(f"Spawning of subprocess that runs the ffmpeg command to produce video is complete, outputs displayed\n")
######################################################

###### selecting subset of xarray for weekly data instead of 365##########################

# Calculates the 7-day rolling min and avg , output are 52 row/week dat

def calculate_weekly_monday_start_single_node(data_array, output_name_prefix, start_date=None, end_date=None):
    """
    Calculates the 7-day rolling minimum *and average*, labeling the result on the Monday that starts each week.
    Adds the final partial week (if any) manually.
    """

    import pandas as pd
    import numpy as np
    import xarray as xr

    # --- Handle default dates if not provided ---
    if start_date is None:
        start_date = data_array['time'].min().item()  # Use earliest time in dataset if no start_date is given
    if end_date is None:
        end_date = data_array['time'].max().item()  # Use latest time in dataset if no end_date is given

    start_date = pd.to_datetime(start_date)  # Ensure datetime format for start_date
    end_date = pd.to_datetime(end_date)  # Ensure datetime format for end_date

    print(f"Start date provided: {start_date.date()}")  # Debug print to show which start date was used

    # --- Find the first Monday on or after the start date ---
    first_monday = start_date + pd.DateOffset(days=(7 - start_date.weekday()) % 7)  # Aligns to next Monday or same day if already Monday
    print(f"Weekly statistics will start on the first Monday on or after this date: {first_monday.date()}")  # Inform user of computed week start

    # --- Filter input data between start_date and end_date ---
    data_filtered = data_array.sel(time=slice(start_date, end_date))  # Keep only time range we're interested in

    # --- Apply 7-day rolling min and average, shifting label to Monday that starts the window ---
    rolling_min = data_filtered.rolling(time=7, min_periods=1).min().shift(time=-6)  # Compute rolling min for each 7-day window, label on first day (Monday)
    rolling_avg = data_filtered.rolling(time=7, min_periods=1).mean().shift(time=-6)  # Same as above but for average instead of min

    # --- Create blank arrays for output results with same shape as input but all NaNs ---
    result_all_days = data_filtered.copy(deep=True)  # Copy structure of filtered data for storing weekly mins
    result_all_days[:] = np.nan  # Fill with NaNs, only Mondays will be updated

    avg_result_all_days = data_filtered.copy(deep=True)  # Prepare similar structure for weekly averages
    avg_result_all_days[:] = np.nan 
    # --- Create list of Mondays to assign values to ---
    mondays = pd.date_range(start=first_monday, end=end_date, freq='W-MON')  # Every Monday within date range (freq='W-MON' ensures weekly Mondays)

    # --- Assign computed rolling values only at Monday timestamps ---
    result_all_days.loc[{'time': mondays}] = rolling_min.sel(time=mondays)  # Only keep results for Mondays in the result array
    avg_result_all_days.loc[{'time': mondays}] = rolling_avg.sel(time=mondays)  # Same but for average

    # --- Extract subset of result arrays for Mondays only ---
    result_weeks_only = result_all_days.sel(time=mondays)  # Just the Monday rows, easier to export or plot
    avg_result_weeks_only = avg_result_all_days.sel(time=mondays)  # Same for average values

    # --- Handle the last partial week (if the last Monday has < 7 days of data left) ---
    last_possible_monday = mondays[-1] if len(mondays) > 0 else None  # Use last computed Monday if list isn't empty
    if last_possible_monday is not None:
        days_remaining = data_filtered.sel(time=slice(last_possible_monday, end_date))  # Get data for last short week (if any)
        if len(days_remaining.time) < 7:
            print(f"Last Monday ({last_possible_monday.date()}) is a short week with {len(days_remaining.time)} days.")  # Debug for awareness
            min_val = days_remaining.min().item()  # Manually compute min for this short week
            avg_val = days_remaining.mean().item()  # Manually compute average for this short week

            result_all_days.loc[{'time': last_possible_monday}] = min_val  # Assign min to full output array
            result_weeks_only.loc[{'time': last_possible_monday}] = min_val  # Assign min to weekly_

    return result_weeks_only, avg_result_weeks_only  # result_weeks_only = min; avg_result_weeks_only = average
