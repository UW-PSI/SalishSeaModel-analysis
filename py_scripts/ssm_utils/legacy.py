# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
# Some updates by Ben Roberts, PSI
import os
from pathlib import Path
import numpy
import pandas as pd
import geopandas as gpd
import xarray as xr
import warnings
from shapely.geometry import Point
from pyproj import CRS, Transformer

def get_nearest_node(shapefile,lats=48.724,lons=-122.576):
    """ Return Salish Sea Model (SSM) node ID, dataframe index and projected
    x-, y- coordinate pair(s) for selected lat/lon location, 
    according to a shapefile representation of the SSM grid. 

    This code is adapted from "find_closest_node_index" https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/SuKyongs_python/find_closest_node_index.py

    It is designed around a shapefile provided by Kevin Bogue
    (https://github.com/RachaelDMueller/KingCounty-Rachael/tree/main/kevin_shapefiles/SSMGrid2_062822) and requires a shapefile
    with attribute names of "lat","lon", and "node_id".
        
    USAGE:
         param [float or numpy array] lats: latitude(s) of selected locations. 
             Default value 48.724 N.
         param [float or numpy array] lons: longitude(s) of selected locations.
             Default value -122.576 E.
         param [string or Path object] shapefile (.shp): combined path and 
             name of SSM shapefile. No default value. 
         return: Four lists of values, all the same length as input lats/lons. 
            [list] node_id(s): SSM node IDs corresponding to input 
             lat(s)/lon(s).
            [list] index: dataframe row index corresponding to node_id(s). 
            [list] station_x: projected lon station locations. 
            [list] station_y: projected lat station locations.
    EXAMPLE:
        node_id, df_index, st_x, st_y = get_nearest_node(
            ssm['shapefile_path'], np.array([48.724, 48.767422, 48.898880]), 
            np.array([-122.57, -122.575792, -122.781905])
        )
    DEVELOPEMENT NOTES:
        This code does not include many error checks. 
        I've identified an example where the nearest node is different
        than I would expect (see, e.g. BHAM-bay location 48.767422 N, 
        -122.575792 E).  This difference is likely due to the way the node
        center is identified.  I haven't put time into evaluating this difference.  
    """
    
    # load shapefile
    try: 
        gdf = gpd.read_file(shapefile)
    except FileNotFoundError:
        print(f'File does not exist: {shapefile}')
    # get shapefile projection information
    shapefile_EPSG = gdf.crs.to_epsg()
    # create transformation from WGS84 to shapefile projection
    transformer = Transformer.from_crs('WGS84',f'EPSG:{shapefile_EPSG}')
    # transform lat(s) and lon(s) to shapefile projection (in meters)
    stations_y, stations_x=transformer.transform(lats, lons) 
    # create vector of SSM model lats and lons 
    # projected to shapefile projection (in meters)
    ssm_y, ssm_x=transformer.transform(gdf.lat, gdf.lon) 
    # calculate distance(s) between lat/lon location(s) and model nodes
    [n_nodes,n_attrs]=gdf.shape
    index=[]
    node_id=[]
    try: # for array of station locations
        # find nearest node index and ID
        for idx in range(0,len(stations_y)):
            distance=(numpy.ones((n_nodes))*stations_x[idx] - ssm_x)**2 + \
                     (numpy.ones((n_nodes))*stations_y[idx] - ssm_y)**2  
            #create boolean vector with True for node with the closest node index 
            # (find the minimum distance between the interested locations 
            #  and node locations)           
            closest_node_index=(distance==numpy.nanmin(distance))
            # get index where True
            index.append(numpy.where(closest_node_index)[0].item())
            # identify nearest SSM node ID(s) to lat/lon locations 
            node_id.append(gdf.node_id[closest_node_index].item())
            
    except: # for single station location
        distance=(numpy.ones((n_nodes))*stations_x - ssm_x)**2 + \
                  (numpy.ones((n_nodes))*stations_y - ssm_y)**2 
        #create boolean vector with True for node with the closest node index 
        # (find the minimum distance between the interested locations 
        #  and node locations)
        closest_node_index=(distance==numpy.nanmin(distance))
        # get index where True
        index.append(numpy.where(closest_node_index)[0].item())
        # identify nearest SSM node ID(s) to lat/lon locations 
        node_id.append(gdf.node_id[closest_node_index].item())
    return node_id,index,stations_x, stations_y


def estimate_nearest_node(shapefile_path, ilat=48.724,ilon=-122.576):
    """
    THIS CODE IS HERE FOR REFERENCE ONLY AND WILL EVENTUALLY GO AWAY B/C IT'S NOT ACCURATE
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees) using Haversine function
    
    Default ilat, ilon values correspond to the Bellingham Bay outfall buoy 
    (NOAA Station 46118)
    
    This script can only run on Hyak and has a hard-coded access to Kevin's shapefile
    
    lat: latitude in decimal degree, e.g. 48.724
    lon: longitude in decimal degree, e.g. -122.576
    """
    try: 
        gdf = gpd.read_file(shapefile_path)
    except FileNotFoundError:
        print(f'File does not exist: {shapefile_path}')
    
    # project lat/lon to shapefile coordinate
    iloc = [Point(xy) for xy in zip([ilon],[ilat])]
    crs = CRS(f'epsg:{gdf.crs.to_epsg()}')
    #crs = CRS('epsg:6318')
    geo_df_iloc = gpd.GeoDataFrame(geometry = iloc, crs = 'WGS84')
    geo_df_iloc = geo_df_iloc.to_crs(crs = crs)
    
    # find nearest polygon to point
    polygon_index = gdf.distance(geo_df_iloc).sort_values().index[0]
    print(polygon_index)
    nearest_node = gdf['node_id'].loc[polygon_index]

    return nearest_node

# reshape_fvcom has been moved to modelio.py

def extract_fvcom_level(gdf, fvcom_timeIJK, LevelNum):
    """ Extract model output at nodes by level. 
    
    param dataframe gdf: geopandas dataframe of FVCOM nodes from 2D planar nodes
        with dimensions of 16012.
    param float fvcom_timeIJK: 3D-FVCOM output in dimensions of time x 160120.
    param int LevelNum: Integer from 1 (surface) to 10 (bottom)
    
    return fvcom_nodeIDs: model output at level in dimension of time x 16012
    """
    if LevelNum not in range(1,11):
        raise ValueError("fvcom_LevelNum must be an integer value from 1-10")

    try:
        node_ids = gdf['node_id'].to_numpy()
    except:
        raise AttributeError("missing 'node_id' column in dataframe")
        
    ijk_index = node_ids * 10 - (11-LevelNum)
    # get DO values at each level
    fvcom_nodeIDs = fvcom_timeIJK[:,ijk_index]
    # if ds['Var_10'] is passed in: 
    # fvcom_nodeIDs = fvcom_timeIJK[:,:].data[:,ijk_index]
    
    return fvcom_nodeIDs

def calc_fvcom_stat(fvcom_output: numpy.array, stat_type: str, axis: int, context_from: list=None):
    """ Perform numpy statistic (e.g. mean, min) on FVCOM_v2.7ecy model output 
        over specific "axis." 
    
    param array(float) fvcom_output: FVCOM_v2.7ecy output array in dimensions of time x 160120.
    param str stat_type: 'min','mean'.
    param int axis: Integer from 0 to ndims(fvcom_output)
    param list(array(float)) context_from: List of arrays of the same dimension as fvcom_output
        (different variables). If given, find and return values from these arrays that are
        coincident with the computed statistic on fvcom_output. Only makes sense if stat_type is
        'min' or 'max'

    return: reduction of model output across specified axis (axs). If context_from specified, returns a
        list starting with the normal reduced output, followed by the corresponding reduction of each
        extra array.
    """
    fvcom_stat = getattr(numpy,stat_type)(fvcom_output,axis=axis)
    if context_from is None:
        return fvcom_stat
    else:
        ret = [fvcom_stat]
        idxs = getattr(numpy,'arg'+stat_type)(fvcom_output,axis=axis, keepdims=True)
        for d in context_from:
            ret.append(
                numpy.squeeze(
                    numpy.take_along_axis(d, indices=idxs, axis=axis),
                    axis=axis)
                )
        return ret

def calc_fvcom_stat_xr(fvcom_output: xr.DataArray, stat_type: str, dim_or_axis, context_from: list=None):
    """xarray wrapper for calc_fvcom_stat that preserves dims/coords"""

    if isinstance(dim_or_axis, str):
        dim = dim_or_axis
        axis = fvcom_output.dims.index(dim)
    else:
        axis = dim_or_axis
        dim = fvcom_output.dims[axis]

    # We have to reimplement context_from using xarray
    fvcom_stat = calc_fvcom_stat(fvcom_output, stat_type, axis)
    if context_from is None:
        return fvcom_stat
    else:
        ret = [fvcom_stat]
        idxs = getattr(fvcom_output,'arg'+stat_type)(dim=dim)
        coords = fvcom_output.coords[dim][idxs]
        for d in context_from:
            # sel takes a slice on the given dimension and accepts an array of indices.
            # But what it returns is a DataArray with a new coordinate named for that
            # collapsed dimension that tracks what indices the data was pulled from.
            # If we keep this new pseudo-coordinate, the DataArray won't be combinable
            # with the fvcom_stat array above. reset_coords is able to drop that new
            # dimension to fix the compatibility problem.
            ret.append(d.sel({dim: coords}).reset_coords(dim, drop=True))
        return ret
