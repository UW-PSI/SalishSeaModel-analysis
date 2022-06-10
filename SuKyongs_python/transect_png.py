#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import os
import datetime
#import netCDF4
from transect_info_calc import transect_info_calc

variable_name=['DO','NH3','NO3','NPP','Temp','Salinity']
variable_unit=['mg/L','mg/L','mg/L','mgC/m2/d',u'\N{DEGREE SIGN}C','ppt']
variable_input=['Var_10','Var_14','Var_15','Var_17','Var_18','Var_19']

#change here according to your need
data_directory='/mmfs1/gscratch/ssmc/USRS/PSI/Adi/BS_WQM/2014_SSM4_WQ_exist1.5_reg/hotstart/outputs'
transect_directory='transect_node_id.csv'
save_directory='/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/graphics/transect'
ivariable= 1 
min_value=5
max_value=10
transect_name='Hood_Canal'
interval_value=0.5

node_info=pd.read_csv('/mmfs1/gscratch/ssmc/USRS/PSI/Kevin/Script/node_info.csv')
scenario_name=data_directory[data_directory[:-17].rfind('/')+1:-17]
date_time=np.array([datetime.datetime(2014,1,1)+datetime.timedelta(days=k) for k in range(0,365)])
siglev=[-0.        , -0.03162277, -0.08944271, -0.16431676, -0.2529822 ,
        -0.35355335, -0.46475795, -0.58566195, -0.7155418 , -0.85381496,-1.]
del_siglev=np.array([siglev[k+1]-siglev[k] for k in range(0,10)])

# read transect node_id
transect_node_index=pd.read_csv(transect_directory).node_id-1

# calculate the daily averaged concentration
temp=netCDF4.Dataset(data_directory+'/s_hy_base000_pnnl007_nodes.nc')
temp_daily_mean=np.mean(np.reshape(temp[variable_input[ivariable-1]][:,:].data,(365,24,16012,10)),axis=1) #time, node (8760, 16012, 10)

transect_depth, transect_distance=transect_info_calc(node_info['x'].values,node_info['y'].values,node_info['depth'],transect_node_index)

from scipy.interpolate import griddata
from scipy import interpolate
import matplotlib.cm as cm
import matplotlib.pyplot as plt

contour_x=transect_distance
contour_y=transect_depth.T #12,26
points=(contour_x.flatten(),contour_y.flatten())
 
idate=1
shape_n=500
contour_z_temp=np.reshape(temp_daily_mean[idate-1,transect_node_index,:],(len(transect_node_index),10)).T
#contour_z_temp=np.reshape(exist_do[0,transect_node_index,:],(len(transect_node_index),10)).T
contour_z=np.append(contour_z_temp[0,:],contour_z_temp)
contour_z=np.append(contour_z,contour_z_temp[-1,:])
contour_z=np.reshape(contour_z,(12,len(transect_node_index)))
        
values=contour_z.flatten()
levels = np.linspace(min_value,max_value,30)

x = contour_x[0,:]
y = contour_y[-1,:]
f = interpolate.interp1d(x, y,kind='cubic')
x_new=np.arange(0,transect_distance[-1,:].max(),step=transect_distance[-1,:].max()/shape_n)
y_new=f(x_new)
    
shape_n=500
date_value=date_time[idate-1]

grid_x, grid_y = np.mgrid[0:np.round(transect_distance[-1,:].max()):500j, np.round(transect_depth[:,-1].min()):0:500j]
mask=[(grid_y<y_new[k+1]) for k in range(0,shape_n-1)]
mask2=(np.array(mask).sum(axis=1)>0)
mask2=np.reshape(np.append((np.ones(shape_n)!=1),mask2),(shape_n,shape_n))
  
grid_z0 = griddata(points, values, (grid_x, grid_y), method='cubic')
grid_z0_mask=np.ma.masked_array(grid_z0, mask = mask2 )

if ivariable==1: #blue-red
    my_cmap = cm.jet_r
    #my_cmap.set_over('midnightblue')
    #my_cmap.set_under('maroon')
else: #red-blue
    my_cmap = cm.jet
    #my_cmap.set_over('maroon')
    #my_cmap.set_under('midnightblue')
    
fig = plt.figure(1,figsize = (12,4))
plt.contourf(grid_x, grid_y, grid_z0_mask, cmap=my_cmap, extend='both',levels=levels)
plt.plot(np.ones(10000)*transect_distance[0,transect_depth.shape[0]-1],np.linspace(0,transect_depth[transect_depth.shape[0]-1,-1],10000),'k',alpha=0.8)
plt.xlim([0,transect_distance[-1,:].max()])
plt.ylim([np.round(transect_depth[:,-1].min()),0])
plt.title(scenario_name+' '+variable_name[ivariable-1]+', '+transect_name+'\nDate:'+str(date_value)[:-9],fontsize=14)
plt.xlabel('[km]', fontsize=12)
plt.ylabel('[m]', fontsize=12)

plt.tick_params(axis="x", labelsize=12)
plt.tick_params(axis="y", labelsize=12)

cbar=plt.colorbar(ticks=np.arange(levels[0],levels[-1]+interval_value,interval_value))
cbar.set_label(label='['+variable_unit[ivariable-1]+']',size=12)
plt.savefig(save_directory+'/'+scenario_name+'_'+variable_name[ivariable-1]+'_'+transect_name+'_'+str(idate)+'.png')
