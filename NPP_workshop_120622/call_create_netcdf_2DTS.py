import pandas as pd
import numpy as np
import yaml
import xarray as xr
import pathlib
import geopandas as gpd
import time
import sys
from create_netcdf_2DTS import create_netcdf_2DTS
"""
 The following commmands needed to be submitting on Hyak before running this code
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

"""
# Use shapefile with inlet attributions, provided by Stefano Mazzilli
shp_dir = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-grid/shapefiles/SSMGrid2_tce_ecy_node_info_v2_10102022_inlets')
shp = shp_dir/'SSMGrid2_tce_ecy_node_info_v2_10102022_inlets.shp'
gdf = gpd.read_file(shp)

# Use 2014 baseline results
nc_dir = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/SSM_model_output/')
nc_file = nc_dir/'NPP_workshop120622_WQM.nc'

with open('../etc/SSM_netcdf_config.yaml', 'r') as config_file:
    ssm_nc = yaml.safe_load(config_file) 
for inlet in ["Bellingham Bay", "Case Inlet", "Sinclair Inlet"]:
    output_netcdf_dir = pathlib.Path(f'/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/NPP_workshop_120622/{inlet.split(" ")[0]}')
    for station_tag in gdf[['Inlet_name','Inlet_info']].groupby('Inlet_info').count().index.to_list()[1:]:
        print("******",inlet,": ",station_tag,"******")
        idx = gdf[gdf['Inlet_info']==station_tag]['tce'].item()
        create_netcdf_2DTS(
           nc_file, 
           output_netcdf_dir, 
           idx
        )    
