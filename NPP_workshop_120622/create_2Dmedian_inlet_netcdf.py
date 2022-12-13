import xarray
import geopandas 
import numpy
import sys

def create_2Dmedian_inlet_netcdf(nc_file, shp_file, output_dir, variable='netPP', inlet_name='Bellingham Bay'):
    '''
    This function returns a 2D array in depth x time of the median across the inlet
    '''
    print(f"Creating 2D netcdf (depth, time) of median, min, and max for {variable} in {inlet_name}")
    # load shapefile with indices specifying inlet nodes
    print("loading shapefile")
    gdf = geopandas.read_file(shp_file)
    # load netcdf of 2014 prediction
    print("loading netcdf")
    ds = xarray.open_dataset(nc_file, format='netcdf4')
    # get indices to select inlet
    idx = (gdf["Inlet_name"]==inlet_name)
    # calculate the median, min, and max for variable across the inlet nodes
    # flip and transpose to orient as depth x time
    print("calculating median, min, and max across inlet for each level and time step")
    if (ds[variable].ndim==3):
        # median
        median = ds[variable][:,:,idx].quantile(0.5, dim='node', skipna=True)
        median = numpy.flip(median.transpose(),axis=0)
        median = median.rename(f"{variable}_median")
        # lower bound
        zero_quantile = ds[variable][:,:,idx].quantile(0, dim='node', skipna=True)
        zero_quantile = numpy.flip(zero_quantile.transpose(),axis=0)
        q_zero = zero_quantile.rename(f"{variable}_quantile_0")
        # upper bound
        one_quantile = ds[variable][:,:,idx].quantile(1, dim='node', skipna=True)
        one_quantile = numpy.flip(one_quantile.transpose(),axis=0)
        q_one = one_quantile.rename(f"{variable}_quantile_1")
        # combine into one xarray
        xr_combined = xarray.merge([median, q_zero, q_one],compat='override')
    elif (ds[variable].ndim==2):
        # median
        median = ds[variable][:,idx].quantile(0.5, dim='node', skipna=True)
        median = numpy.flip(median.transpose(),axis=0)
        median = median.rename(f"{variable}_median")
        # lower bound
        zero_quantile = ds[variable][:,idx].quantile(0, dim='node', skipna=True)
        zero_quantile = numpy.flip(zero_quantile.transpose(),axis=0)
        q_zero = zero_quantile.rename(f"{variable}_quantile_0")
        # upper bound
        one_quantile = ds[variable][:,idx].quantile(1, dim='node', skipna=True)
        one_quantile = numpy.flip(one_quantile.transpose(),axis=0)
        q_one = one_quantile.rename(f"{variable}_quantile_1")
        # combine into one xarray
        xr_combined = xarray.merge([median, q_zero, q_one],compat='override')
    else:
        print(variable, ' has dimensions: ', ds[variable].ndim)
#     print(f"Dimensions of {variable}: ", ds[variable].shape)
#     if stat_type=="median":
#         if (ds[variable].ndim==3):
#             ts2d = ds[variable][:,:,idx].median(axis=2)
            
#         elif (ds[variable].ndim==2):
#             ts2d = ds[variable][:,idx].median(axis=1)
#     if stat_type=="std":
#         if (ds[variable].ndim==3):
#             ts2d = ds[variable][:,:,idx].std(axis=2)
#         elif (ds[variable].ndim==2):
#             ts2d = ds[variable][:,idx].std(axis=1)
    # # flip and transpose to orient as depth x time
    # output_var = numpy.flip(ts2d.transpose(),axis=0)
    # save netcdf to file 
    print(f"saving to: {output_dir/f'{variable}_{inlet_name}_2DLevelsTime.nc'}")
    xr_combined.to_netcdf(
        output_dir/f"{variable}_{inlet_name.split(' ')[0]}_2DLevelsTime.nc",
        format='netcdf4'
    )

if __name__=='__main__':

    args = sys.argv[1:]
    nc_file = args[0]
    shp_file = args[1]
    output_dir = args[2]
    variable = args[3]
    inlet_name = args[4]

    create_2Dmedian_inlet_netcdf(nc_file, shp_file, output_dir, variable, inlet_name)
