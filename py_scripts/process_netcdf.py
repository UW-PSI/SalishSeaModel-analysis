#!/usr/bin/env python3
# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County

import os
import xarray
import yaml
import numpy as np
import geopandas as gpd
import pathlib
import time
import argparse
# load functions from my scripts file "ssm_utils"
from ssm_utils import reshape_fvcom, calc_fvcom_stat

ECOLOGY_VARIABLE_MAP = {
        'temp': 'Var_18',
        'salinity': 'Var_19',
        'DOXG': 'Var_10',
        'NH4': 'Var_14',
        'NO3': 'Var_15',
        'B1': 'Var_12',
        'B2': 'Var_13'
        # TODO finish me
}

def read_netcdf(f, model_var):
    """Read a model output NetCDF file, handling different formats"""
    ds = xarray.open_dataset(f,engine='netcdf4')
    if model_var in ds.variables:
        hourly_values = reshape_fvcom(
            ds[model_var],'days'
        )
    else:
        hourly_values = reshape_fvcom(ds[ECOLOGY_VARIABLE_MAP[model_var]], 'dayslevels')
        hourly_values = np.swapaxes(hourly_values, 2, 3)
    ds.close()
    return hourly_values

def process_netcdf(netcdf_file_path, model_var='DOXG', case='SOG_NB',
                   np_operator='min', bottom_flag=True, surface_flag=False,
                   run_type=None):
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
    with open(pathlib.Path(__file__).parent.parent / 'etc' / f'SSM_config_{case}.yaml', 'r') as file:
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
    if run_type is None:
        run_type = netcdf_file_path.split('/')[-2]

    # create output directory, if it doesn't already exist for all depths
    # see https://docs.python.org/3/library/os.html#os.makedirs
    if os.path.exists(output_base)==False:
        print(f'creating: {output_dir}/{run_type}/wc')
        os.umask(0) #clears permissions
        os.makedirs(output_base, mode=0o777,exist_ok=True)
        os.makedirs(output_dir, mode=0o777,exist_ok=True)
        os.makedirs(output_dir/run_type, mode=0o777,exist_ok=True)
        os.makedirs(output_dir/run_type/'wc', mode=0o777,exist_ok=True)
    elif os.path.exists(output_dir)==False:
        print(f'creating: {output_dir}/{run_type}/wc')
        os.umask(0) #clears permissions
        os.makedirs(output_dir, mode=0o777,exist_ok=True)
        os.makedirs(output_dir/run_type, mode=0o777,exist_ok=True)
        os.makedirs(output_dir/run_type/'wc', mode=0o777,exist_ok=True)
    elif os.path.exists(output_dir/run_type)==False:
        print(f'creating: {output_dir}/{run_type}/wc')
        os.makedirs(output_dir/run_type,mode=0o777,exist_ok=True)
        os.makedirs(output_dir/run_type/'wc',mode=0o777,exist_ok=True)
    else:
        print(f'creating: {output_dir}/{run_type}/wc')
        os.makedirs(output_dir/run_type/'wc',mode=0o777,exist_ok=True)
    # input netcdf filename
    path=netcdf_file_path
    print('***********************************************************')
    print('processing: ', path)
    # load variable into xarray and calculate daily stat (e.g. min)
    hourly_values = read_netcdf(netcdf_file_path, model_var)
    # calculate daily minimum
    daily_values = calc_fvcom_stat(hourly_values, np_operator, axis=1)
    # remove spin-up days
    daily_values_clean = np.delete(
        daily_values,range(0,ssm['run_information']['spin_up_days']),0)
    print('Output file size:',daily_values_clean.shape)

    # store time series of minimum across depth levels & save to file
    print(f'Saving to file:{run_type}/daily_{np_operator}_{model_var}_wc.nc')
    xr_min=xarray.DataArray(daily_values_clean) 
    xr_min.name=f'{model_var}_daily_{np_operator}_wc'
    xr_min.to_netcdf(
        output_dir/run_type/'wc'/f'daily_{np_operator}_{model_var}_wc.nc',
        format='netcdf4'
    )
    # store time series of daily min bottom DO & save to file
    if bottom_flag:
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
    if surface_flag:
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
    parser = argparse.ArgumentParser(description='Create per-variable netcdf extractions of model results')
    parser.add_argument('netcdf_file', type=argparse.FileType('r'), help='input netcdf file path')
    parser.add_argument('model_var', help='variable to extract, e.g. DOXG')
    parser.add_argument('case', help='Experiment case (SOG_NB, whidbey, ...)')
    parser.add_argument('np_operator', help='Daily state (as numpy reduction) to create, e.g. min')
    parser.add_argument('bottom_flag', type=bool, help='Save bottom values to netcdf')
    parser.add_argument('surface_flag', type=bool, help='Save surface values to netcdf')
    parser.add_argument('-t', '--run-type', help='Run type (default is directory name containing model netcdf)')
    args = parser.parse_args()
    # process netcdf
    netcdf_file_path = args.netcdf_file.name
    args.netcdf_file.close()
    process_netcdf(
        netcdf_file_path, args.model_var, args.case, args.np_operator,
        args.bottom_flag, args.surface_flag, run_type=args.run_type)
