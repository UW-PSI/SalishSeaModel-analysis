import pandas as pd
import numpy as np
import yaml
import xarray as xr
import pathlib
import geopandas as gpd
from time import process_time
import sys
from create_TS_ExistRef_netcdf import create_TS_ExistRef_netcdf
"""
The following commmands needed to be submitting on Hyak before running this code
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

"""
# Use shapefile with inlet attributions, provided by Stefano Mazzilli
shp_dir = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-grid/shapefiles/SSMGrid2_tce_ecy_node_info_v2_10102022_inlets')
shp_file = shp_dir/'SSMGrid2_tce_ecy_node_info_v2_10102022_inlets.shp'

# Use 2014 baseline results
nc_dir = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/SSM_model_output/')
nc_exist_file = nc_dir/'NPP_workshop120622_WQM.nc'
nc_ref_file = nc_dir/'NPP_workshop120622_WQM_REF.nc'

with open('../etc/SSM_netcdf_config.yaml', 'r') as config_file:
    ssm_nc = yaml.safe_load(config_file) 
    
for inlet in ["Bellingham Bay", "Case Inlet", "Sinclair Inlet"]:
    output_netcdf_dir = pathlib.Path(
        f'/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/NPP_workshop_120622/{inlet.split(" ")[0]}'
    )
    variable='netPP'
    print("******",inlet,": ",variable,"******")
    start_time = process_time()
    create_TS_ExistRef_netcdf(
        nc_exist_file, 
        nc_ref_file, 
        shp_file, 
        output_netcdf_dir, 
        variable, 
        inlet
    )

    stop_time=process_time()
    elapsed_time = (stop_time - start_time)/60
    print(f'Processing time: {elapsed_time:.2f} minutes')
