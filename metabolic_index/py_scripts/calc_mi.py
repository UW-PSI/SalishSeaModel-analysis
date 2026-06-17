#!/usr/bin/env python3
import os
from argparse import ArgumentParser

import psutil
import numpy as np
import xarray as xr
from scipy.stats import norm
from joblib import Parallel, delayed

from ssm_utils import read_case
from helper_ExportsAndFigs import load_all_nc_datasets, export_dictionary_of_nc_datasets, average_or_select_by_depth_dataset

# Utility Function - Temperature Conversion
kelvin = lambda temperature_c: temperature_c + 273.15  

MAX_JOBS = min(len(os.sched_getaffinity(0)), psutil.cpu_count(logical=False))

# Main Metabolic Index Calculation Function
def calc_mi(pO2, w, temperature, betas, var_covar, method="smr", confidence_level=0.95, parallel=True):
    """
    Calculate the metabolic index (MI) and its confidence interval.

    Parameters:
    - pO2: partial pressure of O2
    - w: body size (g)
    - temperature: degrees Celsius
    - betas: parameter estimates array length 4 (fitted model coefficients??)
    - var_covar: 4x4 variance-covariance matrix (parameter uncertainty)
    - method: 'smr' or other (determines x_predict structure) eg 'smr' (standard metabolic rate) or 'routine' (active metabolism)
    - confidence_level: e.g., 0.95 for 95% CI   

    Returns:
    - dict with keys: mi, lower_bound, upper_bound
    """
    # BR: modified function to accept 1-D vectors natively for
    # performance, and use parallelization for >1-D arrays
    is_scalar = False
    if np.ndim(temperature) != np.ndim(pO2):
        raise ValueError("temperature and pO2 must be the same shape")
    if method not in ('smr','routine'):
        raise ValueError("Invalid method. 'method' should be either 'smr' or 'routine'.")
    if np.ndim(temperature) == 0:
        temperature = np.atleast_1d(temperature)
        pO2 = np.atleast_1d(pO2)
        is_scalar = True
    elif np.ndim(temperature) > 1:
        # A rather lazy approach to dealing with 2+-D arrays.
        # This is of course only going to optimized for certain array
        # shapes, as it parallelizes over the first dimension, iterates
        # over any middle ones, and performs optimized vector computation
        # on the last.
        if parallel:
            rs = Parallel(n_jobs=MAX_JOBS)(
                    delayed(calc_mi)(pO2[i], w, temperature[i], betas, var_covar, method, parallel=False) for i in range(pO2.shape[0])
            )
        else:
            rs = [calc_mi(pO2[i], w, temperature[i], betas, var_covar, method, parallel=False) for i in range(pO2.shape[0])]
        return {k: np.array([r[k] for r in rs]) for k in ('mi','lower_bound','upper_bound')} 
    # From here, consider temperature and pO2 to be vectors of size N

    # Define in function reference values and physical constants (that don't change between organisms or method eg standard/routine metabolism)
    wref = 5  # Reference body weight in grams for scaling 
    tref = 15  # Reference temperature in Celsius for thermal scaling
    kb = 8.617333262145E-5  # Boltzmann constant in eV/K for temperature effects
    # From constants, calculate scaled predictors for allometric and thermal relationships
    # modify logw and inv_temperature:
    logw = np.log(w / wref)  # Log-transform body size ratio for allometric scaling
    inv_temperature = (1 / kb) * (1 / kelvin(temperature) - 1 / kelvin(tref))  # Arrhenius temperature scaling

    # Construct predictor vector (1d array with 4 elements), where we do different things on the last element depending:
    # on whether wish mi based on SMR or on routine metabolism.  If neither, return an error
    # "Vector" format: A 4xN matrix where columns are [intercept, body_size, temperature(i), metabolic_mode: smr/routine]
    x_predict = np.zeros((4, len(inv_temperature)), dtype=float)
    x_predict[0] = -1
    x_predict[1] = logw
    x_predict[2] = inv_temperature
    x_predict[3] = -1 if method == 'smr' else 0

    # Calculate predicted log(MI) using pre-trained model coefficients via matrix algebra
    log_mi_predict = x_predict.T @ betas + np.log(pO2) # Matrix multiplication for linear combination plus oxygen effect
    # Result is shape (N,)

    # shape (N,)
    mi = np.exp(log_mi_predict) # Exponentiate to get maximum ?? likelihood ?? metabolic index value

    # Calculate standard error of log(MI)- Calculate prediction uncertainty using error propagation
    # Quadratic form: x^T * Σ * x for prediction variance, but this
    # assumes x is a vector.
    # This is where BR's changes get complex. x^T * Σ will be shape
    # (N,4), x is shape (4,N), and we want var_pred to be shape (N,).
    # If we just do x^T * Σ * x we get a matrix of shape (N,N), and
    # the diagonal contains the variances we want; the rest is
    # irrelevant. So we can optimize this to just give us the diagonals
    # and not the complete matrix product by taking advantage of numpy
    # broadcasting with the transpose of x^T * Σ.
    # I wouldn't be surprised if there's a more concise way of doing
    # this, but I don't know it.
    var_pred = ((x_predict.T @ var_covar).T * x_predict).sum(axis=0)
    log_mi_se = np.sqrt(var_pred)  # Convert variance to standard error

    # Calculate confidence interval bounds on log scale
    #     Quantile for two-tailed confidence interval
    z_score = norm.ppf(0.5 + confidence_level / 2.0)  # Critical value from standard normal distribution
    #     Confidence interval
    lower_bound = np.exp(log_mi_predict - z_score * log_mi_se)  # Lower bound = mean - critical_value * std_error
    upper_bound = np.exp(log_mi_predict + z_score * log_mi_se)  # Upper bound = mean + critical_value * std_error

    # Return exponentiated values: maximum likelihood, lower and upper bound of CI
    return {
        "mi": mi[0] if is_scalar else mi,
        "lower_bound": np.squeeze(lower_bound) if is_scalar else lower_bound,
        "upper_bound": np.squeeze(upper_bound) if is_scalar else upper_bound
    }

def main():
    parser = ArgumentParser(description='Compute metabolic index for a given species')

    parser.add_argument('case', help='Case name or file')
    parser.add_argument('species', help='Species name as listed in case file')
    parser.add_argument('method', help='routine or smr')

    args = parser.parse_args()

    ssm, case = read_case(args.case)

    taxa = ssm['mi']['species'][args.species]
    encoding = {'zlib': True, 'complevel': 4}

    SSMinputsForMetabolic = {
        'CalMinParam': {
            'pO2_subdir': 'CalMinParam_3D_pO2_daily_min_kPa',
            'pO2_var': 'pO2_daily_min_kPa',
            'temp_subdir': 'CalMinParam_3D_temp_daily_mean_CT',
            'temp_var': 'temp_daily_mean_CT',
        },
        'CalMaxParam': {
            'pO2_subdir': 'CalMaxParam_3D_pO2_daily_max_kPa',
            'pO2_var': 'pO2_daily_max_kPa',
            'temp_subdir': 'CalMaxParam_3D_temp_daily_mean_CT',
            'temp_var': 'temp_daily_mean_CT',
        },
    }

    SSM2014_dic = load_all_nc_datasets('SSM_output/SSM_data_working', [
        'Calculated_WholeYear10Layers_3D_Xarray'
    ])

    SSMcalcs_dic = load_all_nc_datasets('SSM_output/SSM_saturation', [
        'CalMinParam_3D_pO2_daily_min_kPa',
        'CalMinParam_3D_temp_daily_mean_CT',
        'CalMaxParam_3D_pO2_daily_max_kPa',
        'CalMaxParam_3D_temp_daily_mean_CT'
    ])

    output_dir = 'SSM_output/SSM_metabolic'

    for param_type, config in SSMinputsForMetabolic.items():
        print(f"\nProcessing {param_type}...")

        # Direct reference to mapped subdirectories and variables
        pO2_subdir = config['pO2_subdir']
        pO2_var = config['pO2_var']
        temp_subdir = config['temp_subdir']
        temp_var = config['temp_var']

        print(f"  Using pO2 from: {pO2_subdir}[{pO2_var}]")
        print(f"  Using temp from: {temp_subdir}[{temp_var}]")

        # Process each dataset (e.g., 'exist', 'wqm_reference')
        for key in SSMcalcs_dic[pO2_subdir].keys():
            print(f"  Processing dataset: {key}")

            # Direct variable extraction using mapped names
            pO2_data = SSMcalcs_dic[pO2_subdir][key][pO2_var]
            temp_data = SSMcalcs_dic[temp_subdir][key][temp_var]

            print(f"    Data shapes: pO2={pO2_data.shape}, temp={temp_data.shape}")

            # Flatten data for vectorized calculation
            pO2_flat = pO2_data.values.flatten()  # Convert xarray to numpy and flatten
            temp_flat = temp_data.values.flatten()  # Convert xarray to numpy and flatten

            # Apply vectorized metabolic index calculations - 95% CI (confidence_level=0.95) - this is 95/5 not 90/10
            midata = calc_mi(pO2_data, taxa['organism_weight_grams'], temp_data, taxa['betas'], taxa['var_covar'], args.method)

            # Make it a DataArray again
            # TODO add attributes
            mi_xarray = xr.DataArray(midata['mi'], dims=pO2_data.dims,
                                     coords=pO2_data.coords,
                                     name=f'Mindex_{args.species}_{args.method}')
            lower_xarray = xr.DataArray(midata['lower_bound'], dims=pO2_data.dims,
                                     coords=pO2_data.coords,
                                     name=f'Mindex_{args.species}_{args.method}_ci_lower')
            upper_xarray = xr.DataArray(midata['upper_bound'], dims=pO2_data.dims,
                                     coords=pO2_data.coords,
                                     name=f'Mindex_{args.species}_{args.method}_ci_upper')

            # Create separate dictionary keys for each output (matches old workflow pattern)
            mi_key = f"{param_type}_3D_{args.species}_Mindex_{args.method}"

            # Initialize dictionary using subsampled data template (matches current data dimensions by using routine key)
                  # This ensures that the number of nodes and dimensions for 'routine_key' match the current working dataset, whether full or subsampled.
            mi_ds = xr.Dataset({
                f'Mindex_{args.species}_{args.method}': mi_xarray,
                f'Mindex_{args.species}_{args.method}_ci_lower': lower_xarray,
                f'Mindex_{args.species}_{args.method}_ci_upper': upper_xarray
            })
            print(f'Exporting {mi_key}...')
            export_dictionary_of_nc_datasets(
                    dictionary_of_nc_datasets={
                        key: mi_ds
                    },
                    dictionary_name=mi_key,
                    output_dir=output_dir,
                    encoding=encoding
            )

            print('Performing depth averaging...')
            data_2D = average_or_select_by_depth_dataset({key: mi_ds })
            key2d = f"{param_type}_2D_{args.species}_Mindex_{args.method}"
            export_dictionary_of_nc_datasets(
                    dictionary_of_nc_datasets=data_2D,
                    dictionary_name=key2d,
                    output_dir=output_dir,
                    encoding=encoding
            )

            print(f"    ✓ {args.method} metabolic index calculations complete for {key}")

if __name__ == '__main__': main()
