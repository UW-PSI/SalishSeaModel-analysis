#!/bin/bash

#SBATCH --job-name=calc_mi
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=40
#SBATCH --mem=25G
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

CASE=SSM_config_mi.yaml

# Make sure to change these paths to represent your setup
source $HOME/miniforge3/etc/profile.d/conda.sh
export MAMBA_ROOT_PREFIX=$HOME/miniforge3
source $HOME/miniforge3/etc/profile.d/mamba.sh

conda activate psi_mi

for method in routine smr; do
  for species in salmon crab sole; do
    ../py_scripts/calc_mi.py $CASE $species $method
  done
done
