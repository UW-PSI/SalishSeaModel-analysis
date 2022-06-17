import numpy
import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS


def estimate_nearest_node(shapefile_path, ilat=48.724,ilon=-122.576):
    """
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
    crs = CRS('epsg:6318')
    geo_df_iloc = gpd.GeoDataFrame(geometry = iloc, crs = crs)
    geo_df_iloc = geo_df_iloc.to_crs(crs = gdf.crs)
    
    # find nearest polygon to point
    polygon_index = gdf.distance(geo_df_iloc).sort_values().index[0]
    print(polygon_index)
    nearest_node = gdf['node_id'].loc[polygon_index]
#     node = numpy.array(gdf['node_id'])
#     ssmlat,ssmlon = gdf['lat'].values, gdf['lon'].values
    
#     # calculate distance using haversine function
#     dlat = numpy.radians(ssmlat - ilat)
#     dlon = numpy.radians(ssmlon - ilon)
#     r = 6367 # approx. radius of earth in km
#     d = (numpy.sin(dlat/2)**2) + numpy.cos(ilat)*numpy.cos(ssmlat)*(numpy.sin(dlon/2))**2
#     dist = 2*r*numpy.arcsin(numpy.sqrt(d))
    
#     # get the nearest node to input lat/lon pair
#     nearest_node = node[dist == min(dist)].item()
#     print(ssmlat[node==nearest_node], ssmlon[node==nearest_node])
    
    return nearest_node

def reshape_fvcom(fvcom_timeIJK, reshape_type):
    """ Reorganize the 2D FVCOM output from 2-dimensions of (time,nodes)
    to a format that allows for daily, yearly, or depth calculations. 
    
    param float fvcom_timeIJK: FVCOM_v2.7ecy output array in dimension of 8760x160120.
    param string reshape_type: ['days','levels','dayslevels']
    return: Reorganized array
    """
    ti,ni = fvcom_timeIJK.shape
    print(ti,ni)
    # Error handling
    if reshape_type not in ['days','levels','dayslevels']:
        raise ValueError(
            "options for reshape_type are: 'days','levels','dayslevels'"
        )
    
    # Reshaping
    if reshape_type == 'days':
        if (ti != 8760):
            raise TypeError(
                "FVCOM array must have a time dimension of 8760"
            )
        fvcom_reshaped = numpy.reshape(
            fvcom_timeIJK[:,:].data, (365,24,ni)
        )
    elif reshape_type == 'levels':
        if (ni != 160120):
            raise TypeError(
                "FVCOM array must have a node dimension of 160120"
            )
        fvcom_reshaped = numpy.reshape(
            fvcom_timeIJK[:,:].data, (ti,16012,10)
        )
    elif reshape_type == 'dayslevels':
        if (ti != 8760) or (ni != 160120):
            raise TypeError(
                "FVCOM array size must be 8760 x 160120"
            )
        fvcom_reshaped = numpy.reshape(
            fvcom_timeIJK[:,:].data, (365,24,16012,10)
        )
        
    return fvcom_reshaped

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

def calc_fvcom_stat(fvcom_output, stat_type, axis):
    """ Perform numpy statistic (e.g. mean, min) on FVCOM_v2.7ecy model output 
        over specific "axis." 
    
    param float fvcom_output: FVCOM_v2.7ecy output array in dimensions of time x 160120.
    param float stat_type: 'min','mean'.
    param int axis: Integer from 0 to ndims(fvcom_output)
    
    return: stat of model output across specified axis (axs)
    """
    fvcom_stat = getattr(numpy,stat_type)(fvcom_output,axis=axis)
    
    return fvcom_stat


