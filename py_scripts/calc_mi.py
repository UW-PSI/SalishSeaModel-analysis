#!/usr/bin/env python3
# Created by Ben Roberts at the Puget Sound Institute with funding from
# King County

import os
from pathlib import Path
from argparse import ArgumentParser
import time
import logging

import xarray as xr

from ssm_utils import read_case, calc_metabolic_index, FileFinder

def calc_mi(case, ssm_config, species, method):

    logger = logging.getLogger('calc_mi')

    taxa = ssm_config['mi']['species'][species]
    output_dir = Path(ssm_config['paths']['processed_output']) / case
    encoding = {'zlib': True, 'complevel': 4}

    ff_ct = FileFinder(case, ssm_config, 'CT')
    ff_po2 = FileFinder(case, ssm_config, 'pO2')
    ff_out = FileFinder(case, ssm_config, 'mi', mispecies=species,
                        mitype=method, check_exists=False)

    # Input data dictionaries keyed by run type, then min/max/mean
    po2 = {}
    ct = {}
    ds_attrs = {}
    for run_type in ff_po2.run_types:
        po2[run_type] = {}
        # pO2
        logger.info(f'Reading pO2 for {run_type}')
        for agg in ('min','max'):
            p = ff_po2.get_file(run_type, agg)
            with xr.open_dataset(p) as ds:
                if not len(ds_attrs):
                    ds_attrs = ds.attrs
                    logger.info(f'Found dataset attributes {ds.attrs}')
                po2[run_type][agg] = ds[ff_po2.get_var_name(p)]
        # Temp - mean only
        logger.info(f'Reading CT for {run_type}')
        p = ff_ct.get_file(run_type, 'mean')
        with xr.open_dataset(p) as ds:
            ct[run_type] = {'mean': ds[ff_ct.get_var_name(p)] }
    (ndays,nlevels,nnodes) = ct[run_type]['mean'].shape

    logger.info("All data loaded")

    SSMinputsForMetabolic = {
        'min': {
            'pO2': 'min',
            'temp': 'mean'
        },
        'max': {
            'pO2': 'max',
            'temp': 'mean'
        }
    }

    for run_type in ff_po2.run_types:
        for param_type, config in SSMinputsForMetabolic.items():
            logger.info(f"Processing {param_type} for {run_type}...")
            logger.info(f"  Using {config['pO2']} pO2")
            logger.info(f"  Using {config['temp']} temp")

            # Direct variable extraction using mapped names
            pO2_data = po2[run_type][config['pO2']]
            temp_data = ct[run_type][config['temp']]

            logger.info(f"    Data shapes: pO2={pO2_data.shape}, temp={temp_data.shape}")

            # Flatten data for vectorized calculation
            pO2_flat = pO2_data.values.flatten()  # Convert xarray to numpy and flatten
            temp_flat = temp_data.values.flatten()  # Convert xarray to numpy and flatten

            # Apply vectorized metabolic index calculations - 95% CI (confidence_level=0.95) - this is 95/5 not 90/10
            midata = calc_metabolic_index(pO2_data, taxa['organism_weight_grams'],
                                          temp_data, taxa['betas'], taxa['var_covar'], method)

            # Make it a DataArray again
            mi_xarray = xr.DataArray(midata['mi'], dims=pO2_data.dims,
                                     coords=pO2_data.coords,
                                     attrs={'long_name': 'Metabolic Index', 'species': species, 'method': method, 'units': 'none'})
            lower_xarray = xr.DataArray(midata['lower_bound'], dims=pO2_data.dims,
                                        coords=pO2_data.coords,
                                        attrs={'long_name': 'MI lower conf iterval', 'species': species, 'method': method, 'units': 'none'})
            upper_xarray = xr.DataArray(midata['upper_bound'], dims=pO2_data.dims,
                                        coords=pO2_data.coords,
                                        attrs={'long_name': 'MI upper conf interval', 'units': 'none'})

            # Create separate dictionary keys for each output (matches old workflow pattern)
            out_file = ff_out.get_file(run_type, param_type)
            mi_key = ff_out.get_var_name(out_file)

            mi_ds = xr.Dataset({
                mi_key: mi_xarray,
                f'{mi_key}_ci_lower': lower_xarray,
                f'{mi_key}_ci_upper': upper_xarray
            }, attrs=ds_attrs).assign_attrs({
                'species': species,
                'method': method
            })
            logger.info(f'Exporting {mi_key} {species} {method} for {run_type}...')
            out_file.parent.mkdir(parents=True, exist_ok=True)
            mi_ds.to_netcdf(out_file,
                            encoding={k: encoding for k in mi_ds.data_vars.keys()})
 
def main():
    parser = ArgumentParser(description='Compute metabolic index for a given species')

    parser.add_argument('case', help='Case name or file')
    parser.add_argument('species', help='Species name as listed in case file')
    parser.add_argument('method', choices=('routine','smr'), help='routine or smr')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet; suppress most output')

    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO)

    ssm, case = read_case(args.case)

    # Start time counter
    start = time.perf_counter()

    calc_mi(case, ssm, args.species, args.method)

    # End time counter
    end = time.perf_counter()
    logger.info(f'Execution time: {(end - start)/60:.3f} minutes')

if __name__ == '__main__': main()
