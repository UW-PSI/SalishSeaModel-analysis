#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Created on June 8th, 2022 
#This script is for explaining the volume days calculation to Rachael
#If you have question: please contact to SKY (sukyong@uw.edu)


# In[1]:


import numpy as np
import pandas as pd


# In[65]:


#read node information
node_info=pd.read_csv('ecy_node_info_v2.csv', index_col=0) 

#layer distribution
siglev=np.array([  0. ,   3.2,   8.9,  16.4,  25.3,  35.4,  46.5,  58.6,  71.6, 85.4, 100. ])
siglay=np.array([1.6,  6.1, 12.7, 20.9, 30.3, 40.9, 52.5, 65.1, 78.5, 92.7])
siglev_diff=np.array([ 3.2,  5.7,  7.5,  8.9, 10.1, 11.1, 12.1, 13. , 13.8, 14.6])


# In[66]:


#read do data (in here it is radom daily do data)
do_random_np=np.random.uniform(low=1, high=12, size=(365,16012,10)) #day,cell,layer  #between 1mg/l to 12mg/l


# In[70]:


#create numpy with volume information of each layer and cell
lyr_volume_np=(np.ones((10,16012))*node_info['volume'].values).T*siglev_diff/100 #(16012,10)
lyr_time_volume_np=np.ones((365,16012,10))*lyr_volume_np #(365,16012,10)

#calculating hypoxic volume days 
hypoxic_volume_days=lyr_time_volume_np[(do_random_np<2)].sum() #volume days of less 2mg/L


# In[77]:


#adding the filter based on the specific basin 
basin_indicate=node_info['basin_info']=='South Sound'
basin_hypoxic_volume=lyr_time_volume_np[:,basin_indicate,:][do_random_np[:,basin_indicate,:]<2].sum() #364,1028,10

#adding the filter based on the specific basin 
basin_indicate=node_info['basin_info']=='South Sound'
basin_lyr_time_volume_np=lyr_time_volume_np[:,basin_indicate,:] #365,1028,10
basin_do_random_np=do_random_np[:,basin_indicate,:]
basin_hypoxic_volume=basin_lyr_time_volume_np[basin_do_random_np<2].sum() #365,1028,10

#adding the filter based on the specific basin & non-masked & existing DO cells
specific_indicate=(node_info['basin_info']=='South Sound') & (node_info['included_indicator']==1)
specific_hypoxic_volume=lyr_time_volume_np[:,specific_indicate,:][do_random_np[:,specific_indicate,:]<2].sum()

