#!/usr/bin/env python3
# Created by Rachael D. Mueller at the Puget Sound Institute with
# funding from King County
#
# Updates from Ben Roberts allow this script to extract netCDF outputs
# in any of three different formats into a smaller intermediate file.

import os
import pathlib
import time
import glob
import argparse

import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd

# load functions from my scripts file "ssm_utils"
from ssm_utils import reshape_fvcom, calc_fvcom_stat_xr, read_case

ECOLOGY_VARIABLE_MAP = {
        'zeta': 'Var_5',
        'temp': 'Var_18',
        'salinity': 'Var_19',
        'DOXG': 'Var_10',
        'NH4': 'Var_14',
        'NO3': 'Var_15',
        'B1': 'Var_12',
        'B2': 'Var_13'
        # TODO finish me
}

VAR_ATTRS = {
    'DOXG': {'long_name': 'Dissolved Oxygen', 'units': 'mg/L'},
    'temp': {'long_name': 'Temperature', 'units': '°C'},
    'salinity': {'long_name': 'Salinity', 'units': 'PPT'},
    'NO3': {'long_name': 'NO3', 'units': 'N mg/L'},
    'NH4': {'long_name': 'NH4', 'units': 'N mg/L'},
    'B1': {'long_name': 'Phytoplankton B1', 'units': 'g/m3'},
    'B2': {'long_name': 'Phytoplankton B2', 'units': 'g/m3'}
}

# Update this when new features are added to the output file. The script will
# replace existing output files if it detects a version lower than this value.
VERSION = 2

def read_netcdf(files, model_var, start_date=pd.Timestamp('2014.01.01'), hour_reshape=True):
    """Read a model output NetCDF file, handling different formats

    model_var can be a string or a list/array of strings as names
    """
    # See https://stackoverflow.com/a/29319864 for the pattern on accepting scalars or arrays
    # This originally comes from the numpy source but on checking in 2026 it looks like they
    # have changed the pattern
    model_var = np.asarray(model_var)
    scalar_input = False
    if model_var.ndim == 0:
        model_var = model_var[None]
        scalar_input = True

    # First test to see if this is a multi-file glob
    ds = xr.open_mfdataset(files, data_vars=model_var.tolist(), coords=['time']) if len(files) > 1 else xr.open_dataset(files[0])
    if model_var[0] in ds.variables:
        # Note that files made from the text ssm_history files do not
        # have perfectly regular output intervals, so this check has
        # to be approximate
        # (in practice the below check gave a value of 7, so the 40 threshold
        # should be quite safe)
        assert np.abs(np.array(ds['time'][1:]) - np.array(ds['time'][:-1]) - 3600).max() < 40, f'Model output must be hourly'
    hourly_values = []
    nodes = ds['node'].data if 'node' in ds.variables else None # set later
    siglays = ds['siglay'].data if 'siglay' in ds.variables else np.array([ 3.2,  5.7,  7.5,  8.9, 10.1, 11.1, 12.1, 13. , 13.8, 14.6]) / 100
    for v in model_var:
        if v in ds.variables:
            if hour_reshape:
                vals = reshape_fvcom(ds[v],'days')
            else:
                vals = ds[v]
        else:
            data = ds[ECOLOGY_VARIABLE_MAP[v]]
            if hour_reshape:
                vals = reshape_fvcom(data, 'dayslevels')
                vals = np.swapaxes(vals, 2, 3)
            else:
                vals = reshape_fvcom(data, 'levels')
                vals = np.swapaxes(vals, 1, 2)
            if v == 'zeta':
                vals = np.take(vals, 0, axis=vals.ndim-2)
        if nodes is None:
            nodes = np.arange(vals.shape[-1]) + 1
        dims = ['day','hour','siglay','node']
        coords = {
           'day': ('day', start_date + pd.to_timedelta(np.arange(vals.shape[0]), 'day')),
           'hour': ('hour', np.arange(24)),
           'siglay': ('siglay', siglays),
           'node': ('node', nodes)
        }
        if not hour_reshape:
            del coords['hour']
            dims.remove('hour')
            dims.remove('day')
            del coords['day']
            dims.insert(0, 'time')
            coords['time'] = ('time', start_date + pd.to_timedelta(np.arange(vals.shape[0]), 'hour'))
        if v == 'zeta':
            del coords['siglay']
            dims.remove('siglay')
        print(dims)
        print(vals.shape)
        vals = xr.DataArray(data=vals, dims=dims,
                           coords=coords, attrs=VAR_ATTRS.get(v))
        hourly_values.append(vals)
    ds.close()

    return hourly_values[0] if scalar_input else hourly_values

def process_netcdf(netcdf_file_paths: str, model_var='DOXG', case='SOG_NB',
                   np_operator='min', bottom_flag=True, surface_flag=False,
                   run_type=None, if_not_exists=False, phys_context=False):
    """
    *** HEADER INFORMATION TO BE ADDED ***
    model_var options: DOXG, LDOC,B1, B2, NH4, NO3,PO4,temp, salinity, 
                       RDOC, LPOC, RPOC, TDIC, TALK, pH, pCO2
    bottom_flag: [1] to save bottom values to netcdf, [0] to not save
    surface_flag: [1] to save surface values to netcdf, [0] to not save
    """

    if np.ndim(netcdf_file_paths) == 0:
        netcdf_file_paths = netcdf_file_paths[None]

    # load yaml file containing path definitions
    ssm, case = read_case(case)

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
        run_type = netcdf_file_paths[0].split('/')[-2]

    output_wc = output_dir/run_type/'wc'/f'daily_{np_operator}_{model_var}_wc.nc'
    output_bottom = output_dir/run_type/'bottom'/f'daily_{np_operator}_{model_var}_bottom.nc'
    output_surface = output_dir/run_type/'surface'/f'daily_{np_operator}_{model_var}_surface.nc'
    all_outputs = [output_wc]
    if bottom_flag:
        all_outputs.append(output_bottom)
    if surface_flag:
        all_outputs.append(output_surface)
    needed_outputs = []
    for o in all_outputs:
        if if_not_exists and o.is_file():
            # Open this file and check its version
            ds = xr.open_dataset(o)
            v = ds.attrs.get('version')
            ds.close()
            if v is not None and type(v) == np.int64 and int(v) >= VERSION:
                continue
        needed_outputs.append(o)
    if not len(needed_outputs):
        print('All output files already exist, nothing to do')
        return

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

    print('***********************************************************')
    print('processing:', netcdf_file_paths[0])
    # load variable into xarray and calculate daily stat (e.g. min)
    if phys_context:
        hourly_values, hourly_temp, hourly_salt, hourly_el = read_netcdf(netcdf_file_paths,
                [model_var, 'temp', 'salinity', 'zeta'])
        # calculate daily aggregation
        daily_values, daily_temp, daily_salt, daily_el = calc_fvcom_stat_xr(hourly_values, np_operator, 'hour',
                context_from=[hourly_temp, hourly_salt, hourly_el])
        alldata = {
            model_var: daily_values,
            'temp': daily_temp,
            'salinity': daily_salt,
            'zeta': daily_el
        }
    else:
        hourly_values = read_netcdf(netcdf_file_paths, model_var)
        daily_values = calc_fvcom_stat_xr(hourly_values, np_operator, 'hour')
        alldata = { model_var: daily_values }
    # remove spin-up days
    for k in alldata.keys():
        alldata[k] = alldata[k][ssm['run_information']['spin_up_days']:,:]
    print(f'Output file size: {alldata[model_var].shape} x {len(alldata)} vars')

    attrs = {'version': VERSION}

    if output_wc in needed_outputs:
        # store time series of minimum across depth levels & save to file
        print(f'Saving to file:{output_wc}')
        xd_min = xr.Dataset({ f'{k}_daily_{np_operator}{"_wc" if d.ndim == 3 else ""}': d for k,d in alldata.items() }, attrs=attrs)
        xd_min.to_netcdf(output_wc, format='netcdf4')
    else:
        print(f'Skipping creation of {output_wc.basename}')
    # store time series of daily min bottom DO & save to file
    if output_bottom in needed_outputs:
        # create ouptut directory if it doesn't yet exist
        if not output_bottom.parent.is_dir():
            print(f'creating: {output_bottom.parent}')
            os.makedirs(output_bottom.parent, mode=0o777, exist_ok=True)

        print(f'Saving to file:{output_bottom}')
        # Take just the bottom layer, but account for the 2D surface elevation data
        # zeta ends up with a siglay pseudo-coordinate that we need to drop with
        # reset_coords
        daily_values_bottom = {f'{k}_daily_{np_operator}{"_bottom" if d.ndim == 3 else ""}': d.reset_coords('siglay', drop=True) if d.ndim == 2 else d[:,-1,:] for k,d in alldata.items()}
        xd_out = xr.Dataset(daily_values_bottom, attrs=attrs)
        xd_out.to_netcdf(output_bottom, format='netcdf4')
    elif bottom_flag:
        print(f'Skipping creation of {output_bottom.basename}')
    # store time series of daily min surface DO & save to file
    if output_surface in needed_outputs:
        # create ouptut directory if it doesn't yet exist
        if not output_surface.parent.is_dir():
            print(f'creating: {output_surface.parent}')
            os.makedirs(output_surface.parent, mode=0o777, exist_ok=True)

        print(f'Saving to file:{output_surface}')
        # Take just the surface layer, but account for the 2D surface elevation data
        daily_values_sfc = {f'{k}_daily_{np_operator}{"_surface" if d.ndim == 3 else ""}': d.reset_coords('siglay', drop=True) if d.ndim == 2 else d[:,0,:] for k,d in alldata.items()}
        xd_out = xr.Dataset(daily_values_sfc, attrs=attrs)
        xd_out.to_netcdf(output_surface, format='netcdf4')
    elif surface_flag:
        print(f'Skipping creation of {output_surface.basename}')

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Create per-variable netcdf extractions of model results')
    parser.add_argument('netcdf_file', help='input netcdf file path or pattern')
    parser.add_argument('model_var', help='variable to extract, e.g. DOXG')
    parser.add_argument('case', help='Experiment case (SOG_NB, whidbey, ...)')
    parser.add_argument('np_operator', help='Daily state (as numpy reduction) to create, e.g. min')
    parser.add_argument('bottom_flag', type=bool, help='Save bottom values to netcdf')
    parser.add_argument('surface_flag', type=bool, help='Save surface values to netcdf')
    parser.add_argument('-t', '--run-type', help='Run type (default is directory name containing model netcdf)')
    parser.add_argument('--if-not-exists', action='store_true', help="Only do extraction/output if output files aren't already there")
    parser.add_argument('-p','--phys-context', action='store_true',
            help="Include daily physical data from the same hour (for min/max only)")
    args = parser.parse_args()

    # BR: the extraction of zeta later is very slow on the netcdf4 engine
    # because of the slicing. So I have switched to h5netcdf, which is a new
    # addition to the python environment.
    xr.set_options(netcdf_engine_order=['h5netcdf','netcdf4','scipy'],
                       use_new_combine_kwarg_defaults=True)

    netcdf_file_path = sorted(glob.glob(args.netcdf_file))
    if len(netcdf_file_path) == 0:
        raise FileNotFoundError(args.netcdf_file)
    # process netcdf
    process_netcdf(
        sorted(netcdf_file_path), args.model_var, args.case, args.np_operator,
        args.bottom_flag, args.surface_flag, run_type=args.run_type,
        if_not_exists=args.if_not_exists, phys_context=args.phys_context)
