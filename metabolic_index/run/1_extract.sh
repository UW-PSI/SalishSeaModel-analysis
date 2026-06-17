#!/bin/bash

#SBATCH --job-name=extract
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

GSC_HOME=/gscratch/ssmc/USRS/PSI/Ben
GSC_STEFANO=/gscratch/ssmc/USRS/PSI/Stefano
ECY21_EXIST=$GSC_STEFANO/projects/KingCounty/SalishSeaModel/wqm_baseline/ssm_hotstart_wqm_baseline.nc
ECY21_REF=$GSC_STEFANO/projects/KingCounty/SalishSeaModel/wqm_reference/ssm_hotstart_wqm.nc
CASE=SSM_config_mi.yaml

# Make sure to change these paths to represent your setup
source $GSC_HOME/miniforge3/etc/profile.d/conda.sh
export MAMBA_ROOT_PREFIX=$GSC_HOME/miniforge3
source $GSC_HOME/miniforge3/etc/profile.d/mamba.sh

conda activate psi_mi

for method in min mean max; do
  ../py_scripts/process_netcdf.py --if-not-exists --run-type exist $ECY21_EXIST DOXG $CASE $method '' ''
  ../py_scripts/process_netcdf.py --if-not-exists $ECY21_REF DOXG $CASE $method '' ''
done
for model_var in temp salinity; do
  ../py_scripts/process_netcdf.py --if-not-exists --run-type exist $ECY21_EXIST $model_var $CASE mean '' ''
  ../py_scripts/process_netcdf.py --if-not-exists $ECY21_REF $model_var $CASE mean '' ''
done
