# Copyright 2022.  University of Washington Puget Sound Institute's
# Salish Sea Modeling Center. 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Function for calculating the minimum daily value for desired variables. 
This function was developed by Rachael Mueller using code adopted from /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/script/daily_min_data_extract.py.  
It is developed to run on the Hyak supercomputer, at the University of Washington.  

This function can be run in a few ways
## Batch Script (single submission)
```
#!/bin/bash 
#SBATCH --job-name=2014 min values
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1 
#SBATCH --time=1:00:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8

echo  starting the run
date

python daily_min_data_extract_function.py 'DO' '/output-root-directory-path'

date
echo run ended
```
## Batch Script (multiple, simultaneous submissions)
Same as above but with the different run cases included in a file with a `.list` extension, e.g. `2014_bounding_runs.list`, that would look something like: 
```
python x.py 'DO' 'output-directory-path'
python daily_min_data_extract_function.py 'NH3' 'output-root-directory-path/daily_min'
python daily_min_data_extract_function.py 'NO3' 'output-root-directory-path/daily_min'
python daily_min_data_extract_function.py 'NPP' 'output-root-directory-path/daily_min'
python daily_min_data_extract_function.py 'Temp' 'output-root-directory-path/daily_min'
python daily_min_data_extract_function.py 'Salinity' 'output-root-directory-path/daily_min'
```
The batch script above would mostly remain the same, but we would run with glost and need to add a module like
```
module load glost
```
as well as change the `python ...` line to: 
```
echo "Starting run at: `date`"
srun glost_launch /path-to/2014_bounding_runs.list
echo "Finished run at: `date`"
```
So far as I can tell, there is no glost module on hyak so we would need to work with IT support to use this option 
## Command line within an interactive session
First initiate a compute node.  The performance of this code isn't significantly enhanced by more computing power than the following.
```
salloc -A ssmc -p compute -N 1 -c 1 --mem=175G --time=1:00:00
```
followed by
```
module load foster/python/miniconda/3.8
python daily_min_data_extract_function('DO', 'output-directory-path')
```
Note: it has been a minute since I've called a function from command line and need to verify that the above is correct. 
"""
import sys
import pathlib
import time
import numpy 
import pandas 
import os
import datetime
import netCDF4

def main(variable_name, output_path):
    """Enter header information here
    """
    # start time logger
    startTime = time.time()
    # create dictionary called "model_output_name" to map input variable name 
    # to model parameter name
    variable_name_list=['DO','NH3','NO3','NPP','Temp','Salinity']
    parameter_ID_list=['Var_10','Var_14','Var_15','Var_17','Var_18','Var_19']
    model_output_name = {
        variable_name_list[i]: parameter_ID_list[i] for i in range(len(variable_name_list))
    }

    # hardcode list of directories related to scenarios
    # eventually, the directory list will become an input parameter
    #change here according to your need
    root_dir = pathlib.Path('/mmfs1/gscratch/ssmc/USRS/PSI/Adi/BS_WQM/')
    data_paths=numpy.array(
        [root_dir/'2014_SSM4_WQ_rvr1.5_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_rvr0.5_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_rvr0.0_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_rvr_ref_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_rvr_mgt_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist1.5_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist0.5_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist0.0_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist_OBC2.0/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist_OBC1.5/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist_OBC0.5/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist_OBC0.0/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist_CoT_North/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist_CoT_CN/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_exist_CoT_Central/hotstart/outputs',
         root_dir/'2014_SSM4_exist_CoT_Nth_wC/hotstart/outputs',
         root_dir/'2014_SSM4_exist_CoT_Ctl_wC/hotstart/outputs',
         root_dir/'2014_SSM4_exist_CoT_CN_wC/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_wwtp_3mgl_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_wwtp0.0_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_wwtp1.5_reg/hotstart/outputs',
         root_dir/'2014_SSM4_WQ_wwtp0.5_reg/hotstart/outputs'
        ]
    )    
    # Error catch to ensure that variable is included in model output
    try:
        model_output_name[variable_name]
    except ValueError:
        print(f"Incorrect variable name input.  Select from: {variable_name}")
    # Extract min value from list of data_directories
    for si in range(0, len(data_paths)):
        scenario_name=str(data_paths[si]).split('/')[-3]
        print(data_paths[si])
        model_output=netCDF4.Dataset(data_paths[si]/'s_hy_base000_pnnl007_nodes.nc')
        model_output_daily=numpy.reshape(
            model_output[model_output_name[variable_name]][:,:].data, (365,24,160120)
        )
        model_output_daily_min=numpy.min(model_output_daily,axis=1)
        # model_output_daily_min_pd=pandas.DataFrame(model_output_daily_min)
        # model_output_daily_min_pd.to_pickle(
        #     output_path/f'{scenario_name}{variable_name}.pkl'
        # )
        # replace pickle with netcdf output
        model_output_daily_min_xr=xarray.DataArray(
            dailyDO_tmin_bottom[run_type], name='DailyMinBottomDO'
        )
        model_output_daily_min_xr.to_netcdf(
            output_dir/
            f'dailyMinDO_{scenario_name}_{variable_name}.nc'
        )
    
    # display processing time
    executionTime = (time.time() - startTime)
    print(f'Execution time in minutes: {executionTime/60:.2f}')

if __name__ == "__main__":
    args = sys.argv[1:]
    variable_name = args[0]
    output_path = pathlib.Path(args[1])
    main(variable_name, output_path)
