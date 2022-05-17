# Can we do minimum across layers? 
Short answer: Yes, but I'd need to modify the code.  Currently, there is only depth-level information in the 
in Su Kyong's script for `daily_average_data_extract.py`, not `daily_min_data_extract.py`.  The `daily min` script includes all levels in the output, dimension (365,160120).  In the daily average script, on the other hand, I see the following code: 
```
if layer ==0:
    temp2=np.reshape(temp[variable_input[ivariable-1]][:,:].data, (8760, 16012, 10))
    temp3=temp2*del_siglev
    temp_depth_mean=temp3.sum(axis=2) #8760,16012
    temp_daily_mean=np.mean(np.reshape(temp_depth_mean,(365,24,16012)),axis=1)
else:
    temp_daily_mean=np.mean(np.reshape(temp[variable_input[ivariable-1]][:,layer-1:160120:10].data,(365,24,16012)),axis=1)
```
This code gives me insight to how to handle depths in the model output.  
##### Code translation
1. the temporary variable "temp" is reshaped to a 3D form with dimensions of `(time, I x J, 10 depth-levels)` or `(8760, 16012, 10)`
2. the depth-average for the case of `layer==0` is taken as the sum across levels of the "temp" value scaled by `del_siglev`, which is presumably $frac{\Delta$z}{WCT}$ 
3. the daily mean is then the daily-average of the depth-averaged value
4. OR for "else" the daily mean is calculated at a specific depth

##### Minimum across layers
In order to get the Minimum across layers, I would just have to change the code as follows:

1. Reshape "temp" variable to `(time, I x J, 10 depth-levels)`
```
temp2=np.reshape(temp[variable_input[ivariable-1]][:,:].data, (8760, 16012, 10))
```
2. Deal with NaN values if they are set to, e.g., -9999
3. Calculate the minimum value over the depth levels
```
temp_depth_min = temp2.min(axis=2)
```
4. Calculate the minimum value over time
```
temp_daily_min=np.min(np.reshape(temp_depth_min,(365,24,16012)),axis=1)
```

