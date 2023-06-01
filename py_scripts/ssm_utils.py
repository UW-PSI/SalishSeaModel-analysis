# Created by Rachael D. Mueller at the Puget Sound Institute with funding from King County
import numpy
import geopandas as gpd
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

def reshape_fvcom(fvcom_timeIJK, reshape_type):
    """ Reorganize the FVCOM output from 2-dimensions of (time,nodes)
    to a format that allows for daily, yearly, or depth calculations. 
    
    param float fvcom_timeIJK: FVCOM_v2.7ecy output array in dimension of 
        (a) 8760x160120, or 
        (b) .
    param string reshape_type: ['days','levels','dayslevels']
    return: Reorganized array
    """
    # Error handling
    try:
        output_dims = fvcom_timeIJK.ndim
        if output_dims not in [2,3]:
            raise Exception(f'Input array has {output_dims} dimensions, '
                            'but only 2- or 3-dimension arrays are allowed.')
    except ValueError:
        print('ValueError: reshape_fvcom requires a numpy input array')
    
    # 2D output 
    if output_dims == 2:
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
                    "FVCOM array must reflect a 365-day run with a time dimension of 8760"
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
    else:
        ti,zi,ni = fvcom_timeIJK.shape
        print(ti,zi,ni)
        if (ti != 8784):
            raise TypeError(
                "FVCOM array must reflect a 366-day run with a time dimension of 8784"
            )
        fvcom_reshaped = numpy.reshape(
            fvcom_timeIJK[:,:,:].data, (366,24,zi,ni)
        )
        
    return fvcom_reshaped


def reshape_fvcom2D(fvcom_timeIJK, reshape_type):
    """ Reorganize the 2D FVCOM output from 2-dimensions of (time,nodes)
    to a format that allows for daily, yearly, or depth calculations. 
    
    param float fvcom_timeIJK: FVCOM_v2.7ecy output array in dimension of 8760x160120.
    param string reshape_type: ['days','levels','dayslevels']
    return: Reorganized array
    """
    print('***************************************************')
    print('reshape_fvcom2D() is replaced with reshape_fvcom().')
    print('Please update code to use reshape_fvcom()')
    print('***************************************************')
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

def reshape_fvcom3D(fvcom_timeIJK):
    """ Reorganize the 3D FVCOM output from 3-dimensions of (time,nodes)
    to a format that allows for daily, yearly, or depth calculations. 
    
    param float fvcom_timeIJK: FVCOM_v2.7ecy output array in dimension of 8760x10x16012.
    return: Reorganized array
    """
    print('***************************************************')
    print('reshape_fvcom3D() is replaced with reshape_fvcom().')
    print('Please update code to use reshape_fvcom()')
    print('***************************************************')
    
    ti,zi,ni = fvcom_timeIJK.shape
    print(ti,zi,ni)
    if (ti != 8784):
        raise TypeError(
            "FVCOM array must have a time dimension of 8760"
        )
    fvcom_reshaped = numpy.reshape(
        fvcom_timeIJK[:,:,:].data, (366,24,zi,ni)
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


