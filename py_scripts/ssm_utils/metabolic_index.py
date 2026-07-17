# Created by Stefano Mazilli, Tim Essington, and Ben Roberts for the
# Puget Sound Institute with funding provided by King County

import os

import numpy as np
import xarray as xr
from scipy.stats import norm
from joblib import Parallel, delayed

# Utility Function - Temperature Conversion
kelvin = lambda temperature_c: temperature_c + 273.15  

MAX_JOBS = len(os.sched_getaffinity(0))

# Main Metabolic Index Calculation Function
def calc_metabolic_index(pO2, w, temperature, betas, var_covar, method="smr",
                         confidence_level=0.95, parallel=True):
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
                    delayed(calc_metabolic_index)(pO2[i], w, temperature[i], betas, var_covar, method, parallel=False) for i in range(pO2.shape[0])
            )
        else:
            rs = [calc_metabolic_index(pO2[i], w, temperature[i], betas, var_covar, method, parallel=False) for i in range(pO2.shape[0])]
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
