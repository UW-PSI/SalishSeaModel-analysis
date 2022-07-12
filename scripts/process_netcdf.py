import os
import sys
import xarray
import yaml
import numpy as np
import geopandas as gpd
import pathlib
import time
# load functions from my scripts file "ssm_utils"
from ssm_utils import reshape_fvcom3D, calc_fvcom_stat

def process_netcdf(netcdf_file_path):
    output_base = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/slurm_array/')
    graphics_directory = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics')

    model_var = 'DOXG'
    output_dir = output_base/model_var
    run_type = netcdf_file_path.split('/')[-2]
    print(run_type)

    # create output directories if they don't exist for (1) all depths
    if os.path.exists(output_dir)==False:
        print(f'creating: {output_dir}')
        os.makedirs(output_dir)
        os.makedirs(output_dir/run_type)
    # bottom depth only
    if os.path.exists(output_dir/run_type/'bottom')==False:
        print(f'creating: {output_dir}/{run_type}/bottom')
        os.makedirs(output_dir/run_type/'bottom')
        
    with open('../etc/SSM_config.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
    # get shapefile path    
    shp = ssm['shapefile_path']
    # load shapefile into geopandas dataframe
    gdf = gpd.read_file(shp)
    gdf.head(1)
    
    # loop through comparison cases and get timeseries from model output
    #for index,run_type in enumerate(ssm['run_tag']):
#for index,run_type in enumerate([*ssm['run_tag']]):
    # input netcdf filename
    path=netcdf_file_path 
    print('***********************************************************')
    print('processing: ', path)
    # load variable into xarray and calculate daily min.
    ds = xarray.open_dataset(path,engine='netcdf4')
    dailyDO = reshape_fvcom3D(
        ds[model_var]
    )
    ds.close()
    # calculate daily minimum
    dailyDO_tmin = calc_fvcom_stat(dailyDO, 'min', axis=1)

    # store time series of minimum across depth levels & save to file
    print(f'Saving to file:{run_type}/dailyDO_24hrmin.nc')
    xr_minDO=xarray.DataArray(dailyDO_tmin) 
    xr_minDO.name=f'{model_var}24hrMin'
    xr_minDO.to_netcdf(
        output_dir/run_type/f'dailyDO_24hrmin.nc',
        format='netcdf4'
    )
    
    # store time series of daily min bottom DO & save to file
    dailyDO_tmin_bottom = dailyDO_tmin[:,-1,:]
    print(f'Saving to file:{run_type}/bottom/dailyDO_24hrmin_bottom.nc')
    xr_minbotDO=xarray.DataArray(dailyDO_tmin_bottom)
    xr_minbotDO.name=f'{model_var}24hrMinBott'
    xr_minbotDO.to_netcdf(
        output_dir/run_type/'bottom'/f'dailyDO_24hrmin_bottom.nc',
        format='netcdf4'
    )

if __name__=='__main__':
    args = sys.argv[1:]
    if os.path.exists(args[0]):
        process_netcdf(args[0])
    else:
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), args[0]
            )

