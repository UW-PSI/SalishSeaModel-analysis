import xarray
import geopandas 
import numpy
import sys

def create_TS_ExistRef_netcdf(nc_exist_file, nc_ref_file, shp_file, output_dir, variable, inlet_name):
    '''
    This function returns timeseries of median values the inlet for existing, reference, and existing-reference NPP
    '''
    print(f"Creating TS for {variable} in {inlet_name}")
    # load shapefile with indices specifying inlet nodes
    print("loading shapefile")
    gdf = geopandas.read_file(shp_file)
    # get indices to select inlet
    idx = (gdf["Inlet_name"]==inlet_name)
    
    print("calculating median, min, and max across inlet for each level and time step")
    ds_dict={}
    for run in ["exist","ref"]:
        # load netcdf of 2014 prediction
        print("loading netcdf")
        ds = xarray.open_dataset(locals()[f"nc_{run}_file"], format='netcdf4')
        # copy to unique dataarray for difference calculation
        ds_dict[run]=ds.copy()
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
        # save netcdf to file 
        print(f"saving to: {output_dir/f'{variable}_{inlet_name}_{run}_TS.nc'}")
        xr_combined.to_dataframe().to_excel(
            output_dir/f"{variable}_{inlet_name.split(' ')[0]}_{run}_TS.xlsx"
        )
        xr_combined.to_netcdf(
            output_dir/f"{variable}_{inlet_name.split(' ')[0]}_{run}_TS.nc",
            format='netcdf4'
        )
    # Calculate statistice on the difference of Existing - Reference
    difference = ds_dict["exist"][variable] - ds_dict["ref"][variable]
    # median
    median = difference[:,idx].quantile(0.5, dim=['node'], skipna=True)
    median = median.rename(f"{variable}_median")
    # lower bound
    zero_quantile = difference[:,idx].quantile(0, dim=['node'], skipna=True)
    q_zero = zero_quantile.rename(f"{variable}_quantile_0")
    # tenth quantile
    tenth_quantile = difference[:,idx].quantile(.1, dim=['node'], skipna=True)
    q_tenth = tenth_quantile.rename(f"{variable}_quantile_10")
    # ninetieth quantile
    ninetieth_quantile = difference[:,idx].quantile(.9, dim=['node'], skipna=True)
    q_ninetieth = ninetieth_quantile.rename(f"{variable}_quantile_90")
    # upper bound
    one_quantile = difference[:,idx].quantile(1, dim=['node'], skipna=True)
    q_one = one_quantile.rename(f"{variable}_quantile_100")
    # combine into one xarray
    xr_combined = xarray.merge([median, q_zero, q_one, q_tenth, q_ninetieth], compat='override')
    # save netcdf to file 
    print(f"saving to: {output_dir/f'{variable}_{inlet_name}_ExistRef_TS.nc'}")
    xr_combined.to_dataframe().to_excel(
        output_dir/f"{variable}_{inlet_name.split(' ')[0]}_TS_ExistRefDifference.xlsx"
    )
    xr_combined.to_netcdf(
        output_dir/f"{variable}_{inlet_name.split(' ')[0]}_TS_ExistRefDifference.nc",
        format='netcdf4'
    ) 
if __name__=='__main__':

    args = sys.argv[1:]
    nc_exist_file = args[0]
    nc_ref_file = args[1]
    shp_file = args[2]
    output_dir = args[3]
    variable = args[4]
    inlet_name = args[5]

    create_TS_ExistRef_netcdf(nc_exist_file, nc_ref_file, shp_file, output_dir, variable, inlet_name)
