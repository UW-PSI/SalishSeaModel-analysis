# Created by Ben Roberts for Puget Sound Institute with funding from King County

import warnings

import numpy as np
import pandas as pd
import xarray as xr

# Mapping between ecology model output variable names "VAR_*" and the FVCOM-ICM native name
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

# Map for assigning attributes to different parameters
VAR_ATTRS = {
    'DOXG': {'long_name': 'Dissolved Oxygen', 'units': 'mg/L'},
    'pO2': {'long_name': 'Oxygen Partial Pressure', 'units': 'kPa'},
    'temp': {'long_name': 'Temperature', 'units': '°C'},
    'CT': {'long_name': 'Conservative Temperature', 'units': '°C'},
    'salinity': {'long_name': 'Salinity', 'units': 'PPT'},
    'NO3': {'long_name': 'NO3', 'units': 'N mg/L'},
    'NH4': {'long_name': 'NH4', 'units': 'N mg/L'},
    'B1': {'long_name': 'Phytoplankton B1', 'units': 'g/m3'},
    'B2': {'long_name': 'Phytoplankton B2', 'units': 'g/m3'}
}

def reshape_fvcom(fvcom_timeIJK, reshape_type):
    """ Reorganize the FVCOM output from 2-dimensions of (time,nodes)
    to a format that allows for daily, yearly, or depth calculations.

    param float fvcom_timeIJK: FVCOM_v2.7ecy output array in dimension of
        (a) 8760x160120, or
        (b) .
    param string reshape_type: ['days','levels','dayslevels']
    return: Reorganized array
    """
    # Error handling
    try:
        output_dims = fvcom_timeIJK.ndim
    except ValueError:
        print('ValueError: reshape_fvcom requires a numpy input array')
    if output_dims not in [2,3]:
        raise ValueError(f'Input array has {output_dims} dimensions, '
                          'but only 2- or 3-dimension arrays are allowed.')

    # 2D output
    if output_dims == 2:
        ti,ni = fvcom_timeIJK.shape
        print(ti,ni)
        # Error handling
        if reshape_type not in ['days','levels','dayslevels']:
            raise ValueError(
                "options for reshape_type are: 'days','levels','dayslevels'"
            )

        # Reshaping
        if reshape_type == 'days':
            if (ti != 8760):
                raise TypeError(
                    "FVCOM array must reflect a 365-day run with a time dimension of 8760"
                )
            fvcom_reshaped = np.reshape(
                fvcom_timeIJK[:,:].data, (365,24,ni)
            )
        elif reshape_type == 'levels':
            if (ni != 160120):
                raise TypeError(
                    "FVCOM array must have a node dimension of 160120"
                )
            fvcom_reshaped = np.reshape(
                fvcom_timeIJK[:,:].data, (ti,16012,10)
            )
        elif reshape_type == 'dayslevels':
            if (ti != 8760) or (ni != 160120):
                raise TypeError(
                    "FVCOM array size must be 8760 x 160120"
                )
            fvcom_reshaped = np.reshape(
                fvcom_timeIJK[:,:].data, (365,24,16012,10)
            )
    else:
        ti,zi,ni = fvcom_timeIJK.shape
        print(ti,zi,ni)
        if ti/24 != int(ti/24):
            raise TypeError(
                f"FVCOM array must be for a whole number of days"
            )
        if ti != 8784:
            warnings.warn(
                f"FVCOM array should reflect a 366-day run with a time dimension of 8784 (currently {ti})"
            )
        fvcom_reshaped = np.reshape(
            fvcom_timeIJK[:,:,:].data, (int(ti/24),24,zi,ni)
        )

    return fvcom_reshaped

# reshape_fvcom won't accept part of a year as input, so reimplement ourselves. And might as well keep everything in xarray
def reshape_fvcom_xr(fvcom_timeIJK: xr.DataArray, reshape_type, start_date=pd.Timestamp('2014.01.01')):
    try:
        output_dims = fvcom_timeIJK.ndim
    except ValueError:
        print('ValueError: reshape_fvcom_xr requires a DataArray input array')
    if output_dims not in [2,3]:
        raise ValueError(f'Input array has {output_dims} dimensions, '
                          'but only 2- or 3-dimension arrays are allowed.')
    # 2D output
    if output_dims == 2:
        ti,ni = fvcom_timeIJK.shape
        # Error handling
        if reshape_type not in ['days','levels','dayslevels']:
            raise ValueError(
                "options for reshape_type are: 'days','levels','dayslevels'"
            )

        # Prepare new dimensions and coordinates
        if 'days' in reshape_type:
            days = start_date + pd.to_timedelta(np.arange(int(ti/24)), 'day')
            hours = np.arange(24)
            hcoord, dcoord = [arr.flatten() for arr in np.meshgrid(hours, days)]
        else:
            tcoord = start_date + pd.to_timedelta(np.arange(ti), 'hour')
        if 'levels' in reshape_type:
            nodes = np.arange(16012) + 1
            siglays = np.arange(10) + 1
            lcoord, ncoord = [arr.flatten() for arr in np.meshgrid(siglays, nodes)]

        # Reshaping
        if reshape_type == 'days':
            raise ValueError('days is not supported without levels')
        elif reshape_type == 'levels':
            if (ni != 160120):
                raise TypeError(
                    "FVCOM array must have a node dimension of 160120"
                )
            fvcom_reshaped = fvcom_timeIJK.assign_coords(coords={
                'Time': ('Time', tcoord),
                'node': ('IJK', ncoord),
                'siglay': ('IJK', lcoord)
            }).set_index(IJK=('node','siglay')).unstack('IJK')
        elif reshape_type == 'dayslevels':
            if ni != 160120:
                raise TypeError(
                    "FVCOM array size must be size 160120"
                )
            if ti != 8784:
                warnings.warn(
                f"FVCOM array should reflect a 365-day run with a time dimension of 8760 (currently {ti})"
            )
            fvcom_reshaped = fvcom_timeIJK.assign_coords(coords={
                'day': ('Time', dcoord),
                'hour': ('Time', hcoord),
                'node': ('IJK', ncoord),
                'siglay': ('IJK', lcoord)
            }).set_index(Time=('day','hour'), IJK=('node','siglay')).unstack('Time').unstack('IJK')
        else:
            raise ValueError('3D output not supported yet')
    return fvcom_reshaped

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
