#!/bin/bash

#SBATCH --job-name=calc_mi
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=40
#SBATCH --mem=25G
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

for method in routine smr; do
  for species in salmon crab sole; do
    $REPO_HOME/py_scripts/calc_mi.py $CASE $species $method
  done
done
