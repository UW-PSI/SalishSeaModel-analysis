#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#generic 

import numpy as np
import pandas as pd
import os
import datetime
import netCDF4

variable_name=['DO','NH3','NO3','NPP','Temp','Salinity']
variable_input=['Var_10','Var_14','Var_15','Var_17','Var_18','Var_19']
depth_type=['depth_average','lyr1','lyr2','lyr3','lyr4','lyr5','lyr6','lyr7','lyr8','lyr9','lyr10']

#change here according to your need
data_directory='/mmfs1/gscratch/ssmc/USRS/PSI/Adi/BS_WQM/2014_SSM4_WQ_rvr_ref_reg/hotstart/outputs'
save_directory='/mmfs1/home/rdmseas/projects/ssmc/rachael-ssmc/output/gis_output_do'
layer= 0 #start from 1 (surfcae) to 10 (depth) 0 (depth average)
ivariable= 1 

scenario_name=data_directory[data_directory[:-17].rfind('/')+1:-17]
date_time=np.array([datetime.datetime(2014,1,1)+datetime.timedelta(days=k) for k in range(0,365)])
siglev=[-0.        , -0.03162277, -0.08944271, -0.16431676, -0.2529822 ,
        -0.35355335, -0.46475795, -0.58566195, -0.7155418 , -0.85381496,-1.]
del_siglev=np.array([siglev[k+1]-siglev[k] for k in range(0,10)])

temp=netCDF4.Dataset(data_directory+'/s_hy_base000_pnnl007_nodes.nc')
if layer ==0:
    temp2=np.reshape(temp[variable_input[ivariable-1]][:,:].data, (8760, 16012, 10))
    temp3=temp2*del_siglev
    temp_depth_mean=temp3.sum(axis=2) #8760,16012
    temp_daily_mean=np.mean(np.reshape(temp_depth_mean,(365,24,16012)),axis=1)
else:
    temp_daily_mean=np.mean(np.reshape(temp[variable_input[ivariable-1]][:,layer-1:160120:10].data,(365,24,16012)),axis=1) #time, node (8760, 16012)
#temp_daily_mean_pd=pd.DataFrame(temp_daily_mean)
#temp_daily_mean_pd.index=date_time
#temp_daily_mean_pd.to_csv(save_directory+'/'+scenario_name+'_'+variable_name[ivariable-1]+'_'+depth_type[layer]+'.csv')

date_time2=date_time
node=np.ones(365)
for k in range(1,16012):
    node=np.append(node,np.ones(365)*(k+1))
    date_time2=np.append(date_time2,date_time)
    
temp_daily_mean_pd=pd.DataFrame(date_time2, columns=['Date'])
temp_daily_mean_pd.index=node
temp_daily_mean_pd.index.name='Node'
temp_daily_mean_pd['Value']=np.reshape(temp_daily_mean.T, (365*16012))
temp_daily_mean_pd.to_csv(save_directory+scenario_name+'_'+variable_name[ivariable-1]+'_'+depth_type[layer]+'.csv')


