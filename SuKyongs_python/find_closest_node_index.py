#!/usr/bin/env python
# coding: utf-8

# In[11]:


#Created on June 15th, 2022 
#This script is for finding the closest node index of SSM solution
#If you have question: please contact to SKY (sukyong@uw.edu)

import numpy as np 
import pandas as pd
from pyproj import Transformer


# In[7]:


#load node information
node_info=pd.read_excel('ecy_node_info_v2.xlsx',index_col=0)

#change projection type 
transformer = Transformer.from_crs('WGS84',"EPSG:32610")
#interested location information
station_lat=np.array([46.235,45.62067265])
station_lon=np.array([-123.872,-122.6734306])
#changed location information
station_loc_xy=np.array([transformer.transform(station_lat[i],station_lon[i]) for i in range(0,len(station_lon))])

#calculate the distance
distance=(np.ones((16012,2))*station_loc_xy[:,0]-(np.ones((2,16012))*node_info['x'][:].values).T)**2+(np.ones((16012,2))*station_loc_xy[:,1]-(np.ones((2,16012))*node_info['y'][:].values).T)**2
#find the closest node index (find the minimum distance between the interested locations and node locations)
closest_node_index=np.argwhere(distance==np.nanmin(distance,axis=0)).T[0,:]


