import os
import sys
import xarray
import yaml
import numpy as np
import geopandas as gpd
import pathlib
import time
# load functions from my scripts file "ssm_utils"
from ssm_utils import reshape_fvcom, calc_fvcom_stat

def process_netcdf(netcdf_file_path, model_var='DOXG', case='SOG_NB',
                   np_operator='min', bottom_flag=1, surface_flag=0):
    """
    *** HEADER INFORMATION TO BE ADDED ***
    model_var options: DOXG, LDOC,B1, B2, NH4, NO3,PO4,temp, salinity, 
                       RDOC, LPOC, RPOC, TDIC, TALK, pH, pCO2
    bottom_flag: [1] to save bottom values to netcdf, [0] to not save
    surface_flag: [1] to save surface values to netcdf, [0] to not save
    """
    
    # load yaml file containing path definitions.  This file is created by
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.ipynb
    # but can also be modified here (with the caveat the modifications will be 
    # over-written when the SSM_config.ipynb is run
    # https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/etc/SSM_config.yaml
    with open('../etc/SSM_config.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
    
    # load shapefile   
    shp = ssm['paths']['shapefile'] 
    gdf = gpd.read_file(shp)
    
    # define output directory path for storing extracted variables in netcdf files
    print(ssm['paths']['processed_output'])
    output_base = pathlib.Path(ssm['paths']['processed_output'])/case
    print(output_base)
    output_dir = output_base/model_var
    
    # use directory name of model output to define run-type
    run_type = netcdf_file_path.split('/')[-2]
    print(run_type)

    # create output directory, if is doesn't already exist for all depths
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_base)==False:
        print(f'creating: {output_base}')
        os.umask(0) #clears permissions
        os.makedirs(output_base, mode=0o777,exist_ok=True)
    if os.path.exists(output_dir)==False:
        print(f'creating: {output_dir}')
        os.umask(0) #clears permissions
        os.makedirs(output_dir, mode=0o777,exist_ok=True)
    os.makedirs(output_dir/run_type, mode=0o777,exist_ok=True)
   
    # input netcdf filename
    path=netcdf_file_path 
    print('***********************************************************')
    print('processing: ', path)
    # load variable into xarray and calculate daily stat (e.g. min)
    ds = xarray.open_dataset(path,engine='netcdf4')
    hourly_values = reshape_fvcom(
        ds[model_var],'days'
    )
    ds.close()
    # calculate daily minimum
    daily_values = calc_fvcom_stat(hourly_values, np_operator, axis=1)
    # remove first five (spin-up) days
    daily_values_clean = np.delete(daily_values,[0,1,2,3,4],0)
    print('Output file size:',daily_values_clean.shape)

    # store time series of minimum across depth levels & save to file
    print(f'Saving to file:{run_type}/daily_{np_operator}_{model_var}.nc')
    xr_min=xarray.DataArray(daily_values_clean) 
    xr_min.name=f'{model_var}_daily_{np_operator}'
    xr_min.to_netcdf(
        output_dir/run_type/f'daily_{np_operator}_{model_var}.nc',
        format='netcdf4'
    )
    print(bottom_flag)
    # store time series of daily min bottom DO & save to file
    if int(bottom_flag)==1:
        # create ouptut directory if it doesn't yet exist
        if os.path.exists(output_dir/run_type/'bottom')==False:
            print(f'creating: {output_dir}/{run_type}/bottom')
            os.makedirs(
                output_dir/run_type/'bottom',mode=0o777,exist_ok=True
            )

        daily_values_bottom = daily_values_clean[:,-1,:]
        print(f'Saving to file:{run_type}/bottom/daily_{np_operator}_{model_var}_bottom.nc')
        xr_out=xarray.DataArray(daily_values_bottom)
        xr_out.name=f'{model_var}_daily_{np_operator}_bottom'
        xr_out.to_netcdf(
            output_dir/run_type/'bottom'/f'daily_{np_operator}_{model_var}_bottom.nc',
            format='netcdf4'
        )
    # store time series of daily min surface DO & save to file
    if int(surface_flag)==1:
        # create ouptut directory if it doesn't yet exist
        if os.path.exists(output_dir/run_type/'surface')==False:
            print(f'creating: {output_dir}/{run_type}/surface')
            os.makedirs(
                output_dir/run_type/'surface',mode=0o777,exist_ok=True
            )

        daily_values_sfc = daily_values_clean[:,0,:]
        print(f'Saving to file:{run_type}/surface/daily_{np_operator}_{model_var}_surface.nc')
        xr_out=xarray.DataArray(daily_values_sfc)
        xr_out.name=f'{model_var}_daily_{np_operator}_surface'
        xr_out.to_netcdf(
            output_dir/run_type/'surface'/f'daily_{np_operator}_{model_var}_surface.nc',
            format='netcdf4'
        )

if __name__=='__main__':
    """
    VERY basic error handling.  Update needed. 
    # args[0]: input netcdf file path
    # args[1]: variable to extract, e.g. 'DOXG'
    # args[2]: Experiment case (`SOG_NB` or `whidbey`)
    # args[3]: daily stat (as numpy operation) to create, e.g. 'min'
    # args[4]: Boolean flag to save bottom values to netcdf [1] or not [0]
    # args[5]: Boolean flag to save surface values to netcdf [1] or not [0]
    """
    args = sys.argv[1:]
    if len(args)>6:
        raise Error("Too many arguments")
    if len(args)<6:
        raise Error("Too few arguments")
    if os.path.exists(args[0]):
        print("input args:\n", args[0], "\n", args[1], "\n",
              args[2], "\n", args[3], "\n", args[4])
        # assign inputs
        netcdf_file_path = args[0]
        model_var = args[1]
        case = args[2]
        np_operator = args[3]
        bottom_flag = args[4]
        surface_flag = args[5]
        # process netcdf
        process_netcdf(
            netcdf_file_path, model_var, case, np_operator, 
            bottom_flag, surface_flag)
    else:
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), args[0]
            )
