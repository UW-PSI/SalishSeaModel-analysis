import os
import xarray
import yaml
import numpy as np
import geopandas as gpd
import pathlib
import time
# load functions from my scripts file "ssm_utils"
from ssm_utils import reshape_fvcom3D, calc_fvcom_stat


output_base = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data')
graphics_directory = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics')

model_var = 'DOXG'
output_dir = output_base/model_var

# create output directories if they don't exist for (1) all depths
if os.path.exists(output_dir)==False:
    print(f'creating: {output_dir}')
    os.makedirs(output_dir)
# bottom depth only
if os.path.exists(output_dir/'bottom')==False:
    print(f'creating: {output_dir}/bottom')
    os.makedirs(output_dir/'bottom')
    
with open('../etc/SSM_config.yaml', 'r') as file:
    ssm = yaml.safe_load(file)
# get shapefile path    
shp = ssm['shapefile_path']
# load shapefile into geopandas dataframe
gdf = gpd.read_file(shp)
gdf.head(1)

# loop through comparison cases and get timeseries from model output
#for index,run_type in enumerate(ssm['run_tag']):
for index,run_type in enumerate([*ssm['run_tag']]):
    # input netcdf filename
    path=pathlib.Path(
        ssm['output_paths'][index]
    )
    print(path.as_posix())
    # load variable into xarray and calculate daily min.
    ds = xarray.open_dataset(path).load()
    dailyDO = reshape_fvcom3D(
        ds[model_var]
    )
    ds.close()
    # calculate daily minimum
    dailyDO_tmin = calc_fvcom_stat(dailyDO, 'min', axis=1)
    # store time series of minimum across depth levels & save to file
    xr_minDO=xarray.DataArray(dailyDO_tmin) 
    xr_minDO.to_netcdf(output_dir/f'dailyDO_24hrmin_{run_type}.nc')
    
    # store time series of daily min bottom DO & save to file
    dailyDO_tmin_bottom = dailyDO_tmin[:,-1,:]
    xr_minbotDO=xarray.DataArray(dailyDO_tmin_bottom)
    xr_minbotDO.to_netcdf(output_dir/'bottom'/f'dailyDO_24hrmin_bottom_{run_type}.nc')