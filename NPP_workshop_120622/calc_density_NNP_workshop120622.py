import pandas
import numpy
import xarray as xr
import pathlib
import sys
sys.path.insert(1, '/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/seawater')
from seawater import dens

def calc_density(level,idx):
    # Use 2014 baseline results
    nc_dir = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/SSM_model_output/')
    nc_file = nc_dir/'NPP_workshop120622_WQM.nc'
    print('loading netcdf')
    ds = xr.open_dataset(nc_file)
    
    rho = 1024
    g = 9.8
    P = rho*g*ds["depth"]
    
    temp = ds["temp"][:,level,idx]
    salt = ds["salinity"][:,level,idx]
    pressure = P[:,level,idx]
    print('calculating density')
    density = dens(temp,salt,pressure)

    return density

if __name__=='__main__':
    args = sys.argv[1:]
    level=args[0]
    idx = args[1]
    calc_density(level,idx)
