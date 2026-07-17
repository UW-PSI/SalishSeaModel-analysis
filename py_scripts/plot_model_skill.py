#!/usr/bin/env python3

# Created by Ben Roberts at the Puget Sound Institute with funding from King County
#
# This is based heavily on independent code by Ben Roberts at
# https://github.com/bedaro/ssm-analysis/tree/main/validation
# Specifically, ValidateAgainstEcology.ipynb and validation_util.py

import argparse
import os
from pathlib import Path
import glob

import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from ssm_utils import read_case
from ssm_utils.modelio import read_netcdf

# Taken from hydroeval, as this isn't available on conda-forge
def nse(simulations, evaluation):
    """Nash-Sutcliffe Efficiency (NSE) as per `Nash and Sutcliffe, 1970
    <https://doi.org/10.1016/0022-1694(70)90255-6>`_.

    :Calculation Details:
        .. math::
           E_{\\text{NSE}} = 1 - \\frac{\\sum_{i=1}^{N}[e_{i}-s_{i}]^2}
           {\\sum_{i=1}^{N}[e_{i}-\\mu(e)]^2}

        where *N* is the length of the *simulations* and *evaluation*
        periods, *e* is the *evaluation* series, *s* is (one of) the
        *simulations* series, and *μ* is the arithmetic mean.

    """
    nse_ = 1 - (
            np.sum((evaluation - simulations) ** 2, axis=0, dtype=np.float64)
            / np.sum((evaluation - np.mean(evaluation)) ** 2, dtype=np.float64)
    )

    return nse_

# Implemented here instead of adding sklearn as a dependency
def root_mean_squared_error(a: np.array, b: np.array):
    mse = ((b - a) ** 2).mean()
    return np.sqrt(mse)

def run_stats(observed, modeled):
    """Compute model skill statistics

    Compute the standard model performance statistics based on a set of
    observations and model predictions
    """
    rmse = root_mean_squared_error(observed, modeled)
    n = len(observed)
    try:
        fit, stats = np.polynomial.polynomial.Polynomial.fit(observed, modeled, 1, full=True)
        r = np.corrcoef(modeled, fit(observed))[0,1]
    except np.linalg.LinAlgError:
        fit = None
        r = np.nan
    ns = nse(modeled.to_numpy(), observed.to_numpy())
    bias = modeled.mean() - observed.mean()
    return (fit, r, rmse, ns, bias, n)

def plot_fit(ax, observed, modeled, title, unit=None):
    """Build a plot of observed vs modeled data annotated with the fit statistics"""
    plot_margin = 0.05
    fit, r, rmse, ns, bias, n = run_stats(observed, modeled)
    xrange = observed.max() - observed.min()
    xmin = observed.min() - plot_margin * xrange
    xmax = observed.max() + plot_margin * xrange
    yrange = modeled.max() - modeled.min()
    ymin = min(modeled.min() - plot_margin * yrange, xmin)
    ymax = max(modeled.max() + plot_margin * yrange, xmax)
    xbound = np.array((xmin, xmax))
    ax.plot(xbound, xbound, '--', color="gray", linewidth=.7)
    marker = "," if n > 10000 else "."
    ax.plot(observed, modeled, marker)
    ax.plot(xbound, fit(xbound))
    ax.grid()
    lbl_append = " ({0})".format(unit) if unit != None else ""
    ax.set(title=f"{title}\n$R$={r:.2f} RMSE={rmse:.2f} NSE={ns:.2f} Bias={bias:.2f} N={n:d}",
          ybound=(ymin,ymax), xbound=xbound, xlabel="Observed" + lbl_append,
          ylabel="Model Predicted" + lbl_append)

# The mapping structure needed to work with Ecology's pairings files
COL_NAMES = {
    'Temperature': {     # Readable name of constituent (used for plotting)
        'col': 'Temp_C', # Column name in spreadsheet
        'var': 'temp'    # Corresponding model output variable name
    },
    'Salinity': {
        'col': 'Salinity_psu',
        'var': 'salinity'
    },
    'Dissolved Oxygen': {
        'col': 'DO_mgL',
        'var': 'DOXG'
    },
    'Chlorophyll-A': {
        'col': 'Chla_ugL',
        'var': ('B1','B2'), # var can be a sequence, meaning the variables will be summed
        'ratio': (1000/37, 1000/50) # A multiple used for unit conversion.
                                    # Needs to match dimensions of var.
    },
    'Nitrate': {
        'col': 'NO23N_mgL',
        'var': 'NO3'
    },
    'Ammonia': {
        'col': 'NH4N_mgL',
        'var': 'NH4'
    }
}

# FIXME handle missing data in model output file
def calc_model_skill(model_output_path: list, model_obs_pair_file: str):
    pairings = pd.read_excel(model_obs_pair_file, parse_dates=[1])
    nodes = np.sort(pairings['Nodes'].unique())
    start_dt = pd.Timestamp(year=pairings['Model_Time'].dt.year[0], month=1, day=1)

    # Read in all the model data, then save just the nodes we need and do the
    # necessary sums and unit conversions. This saves a ton of memory and front-loads
    # a bit of complexity.
    print('Reading model data...')
    model_output_data = {}
    for k,coldata in COL_NAMES.items():
        try:
            print(k)
            # Reading the variables one-at-a-time like this works fine on
            # single-file model outputs, but on the multi-file datasets this is
            # incredibly slow. Resolving this without devouring RAM would require
            # building the node-reduction capability into read_netcdf
            model_data_all = read_netcdf(model_output_path, coldata['var'])
            # subsample down to just the nodes we need to save memory
            if np.ndim(coldata['var']) == 1:
                ratios = coldata['ratio'] if 'ratio' in coldata else np.ones_like(coldata['var'])
                model_data = model_data_all[0][:,:,:,nodes-1] * ratios[0]
                for i,r in enumerate(ratios[1:]):
                    model_data += model_data_all[i+1][:,:,:,nodes-1] * r
            else:
                model_data = model_data_all[:,:,:,nodes-1] * (coldata['ratio'] if 'ratio' in coldata else 1)
            model_output_data[k] = model_data
        except ValueError:
            # This usually indicates the variable isn't present in the output,
            # so skip it
            print('(not found, skipped)')

    # Later we're going to use .loc[] to index the DataArrays, and for that we need
    # to match siglay values to ordinal indices. Do that now
    siglays = model_output_data[next(iter(model_output_data.keys()))].coords['siglay']

    # read_netcdf gives us data in shape (days,hours,layers,nodes) so to index
    # that we need to separate the date (day) from the hour
    dates = pairings['Model_Time'].dt.date
    hours = pairings['Model_Time'].dt.hour

    # Erase the existing model data
    for cst,coldata in COL_NAMES.items():
        pairings['Model_' + coldata['col']] = np.nan

    print('Performing pairings by node...')
    # The goal here is to update the "data" DF with values extracted from
    # model_output_data. That requires using the "df.loc[] = values" pattern
    # so we need to build a selector for all present combinations of 3 total
    # dimensions: node, time, and depth.
    # To do that, we can use nested groupby calls, but we cannot update the
    # "group" variables directly. Instead we have to keep track of all the
    # groupby conditions in the form of an indexer that can eventually be
    # passed to .loc[]
    count_n = pairings['Nodes'].nunique()
    for i,(n,group) in enumerate(pairings.groupby('Nodes')):
        node_selector = (pairings['Nodes'] == n)
        for t,group2 in group.groupby('Model_Time'):
            t_selector = (pairings['Model_Time'] == t)
            for l,group3 in group2.groupby('Layer'):
                selector = node_selector & t_selector & (pairings['Layer'] == l)
                lay = siglays[l-1]
                for cst,d in model_output_data.items():
                    coldata = COL_NAMES[cst]
                    value = d.loc[np.datetime64(t.date()),t.hour,lay,n]
                    pairings.loc[selector, 'Model_' + coldata['col']] = value
        if (i + 1) % 10 == 0:
            print(f'{i+1}/{count_n}')

    return pairings

def main():
    parser = argparse.ArgumentParser(description='Assemble and plot model skill data')
    parser.add_argument('case', help='Case name or file')
    parser.add_argument('run_tag', nargs='?', help='Tag of run to check skill on')

    args = parser.parse_args()

    xr.set_options(netcdf_engine_order=['h5netcdf','netcdf4','scipy'],
                       use_new_combine_kwarg_defaults=True)

    ssm, case = read_case(args.case)
    run_tag = args.run_tag if args.run_tag is not None else ssm['run_information']['baseline']

    pairings_path = ssm['paths']['pairings_file']
    # model outputs are a simple array so we need to be a bit clever to match path to run tag
    model_outputs = ssm['paths']['model_output'][case]
    assert run_tag in ssm['run_information']['run_tag'][case], f'{run_tag} not found in run_information (found {ssm["run_information"]["run_tag"][case].keys()}'
    model_output_path = sorted(glob.glob(model_outputs[list(ssm['run_information']['run_tag'][case].keys()).index(run_tag)]))

    data = calc_model_skill(model_output_path, pairings_path)

    excel_output_path = Path(ssm['paths']['spreadsheets'])
    if not excel_output_path.is_dir():
        print(f'creating: {excel_output_path}')
        excel_output_path.mkdir(parents=True)
    print('*************************************************************')
    print('Writing spreadsheet to:', excel_output_path)
    print('*************************************************************')
    data.to_excel(excel_output_path / f'model_skill_{run_tag}.xlsx', index=False)

    graphics_output_path = Path(ssm['paths']['graphics'])
    if not graphics_output_path.is_dir():
        print(f'creating: {graphics_output_path}')
        os.umask(0) #clears permissions
        graphics_output_path.mkdir(parents=True)
    print('*************************************************************')
    print('Writing plots to:', graphics_output_path)
    print('*************************************************************')
    for cst,coldata in COL_NAMES.items():
        fig, ax = plt.subplots()
        colname = coldata['col']
        unit = colname.split('_')[-1]
        data_sub = data.dropna(subset=(colname, 'Model_' + colname))
        if data_sub.empty:
            print(f'No data for {cst}, skipping plot')
            continue
        plot_fit(ax, data_sub[colname], data_sub['Model_' + colname], cst, unit=unit)
        filename = f'model_skill_{run_tag}_{colname}.png'
        fig.savefig(graphics_output_path / filename)
        plt.close(fig)

if __name__ == '__main__': main()
