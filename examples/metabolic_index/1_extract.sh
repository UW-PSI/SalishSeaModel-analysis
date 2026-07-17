#!/bin/bash

#SBATCH --job-name=extract
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

trap "kill 0" SIGINT # Ensure subprocesses are killed on interrupt

for method in min mean max; do
  $REPO_HOME/py_scripts/process_netcdf.py --if-not-exists exist DOXG $CASE $method &
  $REPO_HOME/py_scripts/process_netcdf.py --if-not-exists wqm_reference DOXG $CASE $method &
  wait
done
for model_var in temp salinity; do
  $REPO_HOME/py_scripts/process_netcdf.py --if-not-exists exist $model_var $CASE mean &
  $REPO_HOME/py_scripts/process_netcdf.py --if-not-exists wqm_reference $model_var $CASE mean &
  wait
done
