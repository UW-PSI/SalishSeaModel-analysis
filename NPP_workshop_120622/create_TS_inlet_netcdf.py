import xarray
import geopandas 
import numpy
import sys

def create_TS_inlet_netcdf(nc_file, shp_file, output_dir, variable='netPP', inlet_name='Bellingham Bay'):
    '''
    This function returns a 1D time series of the median, min, max, 10% quantile and 90% quantile across the inlet
    '''
    print(f"Creating timeseries of median, min, max, 10th and 90th quantiles for {variable} in {inlet_name}")
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
    print("calculating median, min, max, 10th and 90th quantiles across inlet for each time step")
    if (ds[variable].ndim==3):
        if variable in ["B1","B2","NO3"]:
            modified_variable = ds[variable][:,:,idx].sum(dim='siglay')
        elif variable in ["DOXG"]:
            modified_variable = ds[variable][:,:,idx].min(dim='siglay')
        elif variable in ["salinity","temp"]:
            modified_variable = ds[variable][:,0,idx]
        else:
            return
        # median
        median = modified_variable.quantile(0.5, dim=['node'], skipna=True)
        median = median.rename(f"{variable}_median")
        # lower bound
        zero_quantile = modified_variable.quantile(0, dim=['node'], skipna=True)
        q_zero = zero_quantile.rename(f"{variable}_quantile_0")
        # tenth quantile
        tenth_quantile = modified_variable.quantile(.1, dim=['node'], skipna=True)
        q_tenth = tenth_quantile.rename(f"{variable}_quantile_10")
        # ninetieth quantile
        ninetieth_quantile = modified_variable.quantile(.9, dim=['node'], skipna=True)
        q_ninetieth = ninetieth_quantile.rename(f"{variable}_quantile_90")
        # upper bound
        one_quantile = modified_variable.quantile(1, dim=['node'], skipna=True)
        q_one = one_quantile.rename(f"{variable}_quantile_100")
        # combine into one xarray
        xr_combined = xarray.merge([median, q_zero, q_one, q_tenth, q_ninetieth],compat='override')
    elif (ds[variable].ndim==2):
        # median
        median = ds[variable][:,idx].quantile(0.5, dim=['node'], skipna=True)
        median = median.rename(f"{variable}_median")
        # lower bound
        zero_quantile = ds[variable][:,idx].quantile(0, dim=['node'], skipna=True)
        q_zero = zero_quantile.rename(f"{variable}_quantile_0")
        # tenth quantile
        tenth_quantile = ds[variable][:,idx].quantile(.1, dim=['node'], skipna=True)
        q_tenth = tenth_quantile.rename(f"{variable}_quantile_10")
        # ninetieth quantile
        ninetieth_quantile = ds[variable][:,idx].quantile(.9, dim=['node'], skipna=True)
        q_ninetieth = ninetieth_quantile.rename(f"{variable}_quantile_90")
        # upper bound
        one_quantile = ds[variable][:,idx].quantile(1, dim=['node'], skipna=True)
        q_one = one_quantile.rename(f"{variable}_quantile_100")
        # combine into one xarray
        xr_combined = xarray.merge([median, q_zero, q_one, q_tenth, q_ninetieth], compat='override')
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
    # save to excel
    print(f"saving to: {output_dir/f'{variable}_{inlet_name}_TS.xlsx'}") 
    xr_combined.to_dataframe().to_excel(
        output_dir/f"{variable}_{inlet_name.split(' ')[0]}_TS.xlsx"
    )
    # save netcdf to file 
    print(f"saving to: {output_dir/f'{variable}_{inlet_name}_TS.nc'}")
    xr_combined.to_netcdf(
        output_dir/f"{variable}_{inlet_name.split(' ')[0]}_TS.nc",
        format='netcdf4'
    )

if __name__=='__main__':

    args = sys.argv[1:]
    nc_file = args[0]
    shp_file = args[1]
    output_dir = args[2]
    variable = args[3]
    inlet_name = args[4]

    create_TS_inlet_netcdf(nc_file, shp_file, output_dir, variable, inlet_name)
