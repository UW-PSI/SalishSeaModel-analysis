import xarray
import geopandas 
import numpy
import sys

def create_netcdf_2DTS(nc_file, output_dir, idx):
    '''
    This function returns a 2D array in depth x time for the given node_id (idx)
    '''
    print(f"Creating 2D netcdf (depth, time) for node {idx}")
    # load netcdf of 2014 prediction
    print("loading netcdf")
    run_id = str(nc_file).split('_')[-1].split('.')[0]
    print("run_id: ", run_id)
    ds = xarray.open_dataset(nc_file, format='netcdf4')
    # Save timeseries information for all 2D and 3D variables in output netcdf
    variable_list=[]
    xr_combined_list=[]
    for variable in [*ds]:
       print(f'Adding timeseries for: {variable}')
       if (ds[variable].ndim==3):
           locals()[variable] = ds[variable][:,:,idx]
           xr_combined_list.append(locals()[variable])
           #print(locals()[variable])
           variable_list.append(variable)
       elif (ds[variable].ndim==2):
           locals()[variable] = ds[variable][:,idx]
           xr_combined_list.append(locals()[variable])
           #print(locals()[variable])
           variable_list.append(variable)
       else:
           print(variable, ' has dimensions: ', ds[variable].ndim)
    print(f"saving to: {output_dir/f'2DTS_node_{idx}_{run_id}.nc'}")
    #xr_combined = xarray.merge(locals()[variable_list],compat='override')
    xr_combined = xarray.combine_by_coords(xr_combined_list)
    xr_combined.to_netcdf(
        output_dir/f"2DTS_node_{idx}_{run_id}.nc",
        format='netcdf4'
    )

if __name__=='__main__':

    args = sys.argv[1:]
    nc_file = args[0]
    output_dir = args[1]
    idx = args[2]

    create_netcdf_2DTS(nc_file, output_dir, idx)
