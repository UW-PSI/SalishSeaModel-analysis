#!/usr/bin/env python3

# Python builtins
import os
import argparse
import time
from pathlib import Path
import logging

# Third party libraries
import xarray as xr
import geopandas as gpd

from ssm_utils import read_case, FileFinder, ExposureReturn

def exposure_return(case: str, ssm_config: dict,
                      threshold: float, vtype: str = 'DOXG',
                      mitype: str = None, mispecies: str = None,
                      run_type: str = None):

    logger = logging.getLogger('exposure_return')

    # Define dimension sizes and load shapefile
    shp = ssm_config['paths']['shapefile']
    gdf = gpd.read_file(shp).set_index('tce')
    if len(gdf) == 16013:
        logger.warning('Correcting shapefile length')
        gdf = gdf.iloc[:-1].copy()
    gdf = gdf.rename(columns={'region_inf':'Regions'})
    regions = gdf[['node_id','Regions']].groupby('Regions').count().index.to_list()

    # Get path for model output
    ff = FileFinder(case=case, ssm_config=ssm_config, vtype=vtype,
                    mitype=mitype, mispecies=mispecies, run_type=run_type)
    output_var_base = ff.output_var_base

    output_dir = Path(ssm_config['paths']['processed_output']) / case / 'ExposureReturn' / f'{output_var_base}_ExposureReturn_lt{threshold}'
    if not output_dir.is_dir():
        output_dir.mkdir(parents=True)

    # Now, load files
    data = {}
    attrs = {}
    for run_type in ff.run_types:
        data[run_type] = {}
        for agg in ('min','max'):
            p = ff.get_file(run_type, agg)
            with xr.open_dataset(p) as ds:
                if not len(attrs):
                    attrs = ds.attrs
                data[run_type][agg] = ds[ff.get_var_name(p)]

    er = ExposureReturn(ssm_config, gdf, data[run_type][agg].sizes)

    for run_type in ff.run_types:
        logger.info(f'Processing run {run_type}')
        # PERFORM THE EXPOSURE/RETURN COMPUTATION
        er.apply(data[run_type]['min'] < threshold, data[run_type]['max'] < threshold)

        # FULL NETCDF CREATION AND OUTPUT
        attrs = data[run_type]['min'].attrs.copy()
        attrs['threshold'] = threshold
        ds = xr.Dataset(data_vars={
            f'{output_var_base}_{run_type}_exposure': er.exposure.assign_attrs({
                'long_name': 'Exposure duration by date of start',
                'units': 'days'
            }),
            f'{output_var_base}_{run_type}_returntime': er.return_time.assign_attrs({
                'long_name': 'Return time by date of start',
                'units': 'days'
            }),
            f'{output_var_base}_{run_type}_partial': er.partial_return.assign_attrs({
                'long_name': 'Partial return by date of start',
                'description': 'When daily max goes above threshold',
                'units': 'days'
            }),
            f'{output_var_base}_{run_type}_net': er.net_exposure.assign_attrs({
                'long_name': 'Net exposure (exposure not counting partial return) by date of start',
                'units': 'days'
            })
        }, attrs=attrs)
        ds.to_netcdf(output_dir / f'{run_type}.nc', encoding={v: {'dtype': 'u2', '_FillValue': 0, 'zlib': True, 'complevel': 4} for v in ds.data_vars.keys()})

    return output_var_base

def main():
    parser = argparse.ArgumentParser(description='Compute exposure and return times below a threshold')
    parser.add_argument('case', help='Case name or file')
    parser.add_argument('threshold', type=float, default=2, help='Threshold value')
    subparsers = parser.add_subparsers(title='Data type selection')
    parser_var = subparsers.add_parser('var', help='Work with a model output variable')
    parser_var.add_argument('variable', help='Output variable, like DOXG')
    parser_var.set_defaults(mode='var')

    parser_mi = subparsers.add_parser('mi', help='Work with metabolic index data')
    parser_mi.add_argument('species', help='Species tag')
    parser_mi.add_argument('type', choices=('routine','smr'), help='routine or smr')
    parser_mi.set_defaults(mode='mi', variable='MI')

    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    # Start time counter
    start = time.perf_counter()

    ssm_config, case = read_case(args.case)

    if args.mode == 'mi':
        base = exposure_return(case, ssm_config, args.threshold, 'mi', mitype=args.type,
                                   mispecies=args.species)
    else:
        base = exposure_return(case, ssm_config, args.threshold, args.variable)

    # End time counter
    end = time.perf_counter()
    logger.info(f'Execution time: {(end - start)/60:.3f} minutes')

if __name__ == '__main__': main()
