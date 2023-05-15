#!/bin/bash

## job name 
#SBATCH --job-name=stations

#SBATCH --account=ssmc
#SBATCH --partition=compute 

## Resources 
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=40 
#SBATCH --time=24:00:00 
#SBATCH --mem=175G 

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
echo  starting the run
date

#pip install xlsxwriter

python QAQC_stations.py

date
echo run ended
