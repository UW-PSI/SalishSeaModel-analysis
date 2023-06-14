#!/bin/bash
# Created by Rachael D. Mueller at the Puget Sound Institute with funding by King County
 
## job name 
#SBATCH --job-name=process_netcdf
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-1
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

case="main"

## Uncomment one of the three options below
## ~~~ OPTION 1 ~~~
##param="NO3"
##stat_type="mean"

## ~~~ OPTION 2 ~~~
#param="salinity"
#stat_type="mean"

## ~~~ OPTION 2 ~~~
param="DOXG"
stat_type="min"


if [ $case == "SOG_NB" ]; then

   echo "SOG_NB case"

   run_folders=(
   "1b_all_sog_wwtp_off"
   "1c_all_sog_riv_off"
   "1d_small_sog_wwtp_off"
   "wqm_baseline"
   "wqm_reference"
   "1e_med_sog_wwtp_off"
   "2a_sog_river_0.5times"
   "2b_sog_river_2times"
   )
  
   file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/\
   ${run_folders[${SLURM_ARRAY_TASK_ID}]}/ssm_output.nc"	

   py_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"
   echo ${file_path}
   python ${py_path}/process_netcdf.py ${file_path} ${param} ${case} ${stat_type} 1 1 

elif [ $case == "whidbey" ]; then

   echo "whidbey case"

   file_path=(
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_baseline/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_reference/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3b/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3c/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3e/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3f/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3g/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3h/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3i/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/3j/ssm_hotstart_rdm.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/3k/ssm_hotstart_rdm.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/3l/ssm_hotstart_rdm.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3m/ssm_output.nc"
   )
   
   

   py_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"
   echo ${file_path}
   python ${py_path}/process_netcdf.py  ${file_path[${SLURM_ARRAY_TASK_ID}]} ${param} ${case} ${stat_type} 1 1 

elif [ $case == "whidbeypers" ]; then

   echo "pers case"

   file_path=(
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_baseline/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_reference/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3c/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/3l/ssm_hotstart_rdm.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/3m/ssm_output.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/3n/ssm_hotstart_3n.nc"
   "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/3o/ssm_hotstart_3o.nc"
   ) 

   py_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"
   echo ${file_path}
   python ${py_path}/process_netcdf.py  ${file_path[${SLURM_ARRAY_TASK_ID}]} ${param} ${case} ${stat_type} 1 1 
   
elif [ $case == "main" ]; then

   echo "main case"
   
   file_path=(
    "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/4b/ssm_hotstart_4b.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/4c/ssm_hotstart_4c.nc"
   )   
   
   py_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"
   
   python ${py_path}/process_netcdf.py  ${file_path[${SLURM_ARRAY_TASK_ID}]} ${param} ${case} ${stat_type} 1 1 
   
    file_path=(
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_baseline/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_reference/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/4b/ssm_hotstart_4b.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/4c/ssm_hotstart_4c.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4d/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4e/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4f/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4g/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4h/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4i/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4j/ssm_output.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/4k/ssm_hotstart_4k.nc"
    "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/4l/ssm_output.nc"
    )

    py_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"
    echo ${file_path}
    python ${py_path}/process_netcdf.py  ${file_path[${SLURM_ARRAY_TASK_ID}]} ${param} ${case} ${stat_type} 1 1 

else

   echo "Error: Specify either SOG_NB or whidbey as case"

fi

