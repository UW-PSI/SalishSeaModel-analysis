#!/bin/bash

 

## job name 
#SBATCH --job-name=BS_2st


#SBATCH --account=ssmc
#SBATCH --partition=compute
## Resources 
## Nodes 
#SBATCH --nodes=1       
## Tasks per node (Slurm assumes you want to run 28 tasks per node unless explicitly told otherwise)
#SBATCH --ntasks-per-node=1 
## Walltime (hh:mm:ss) 
#SBATCH --time=24:00:00 
## Memory per node 
#SBATCH --mem=175G 

## Modules needed to run
module purge
module load foster/python/miniconda/3.8

echo  starting the run
date

python transect_png.py

date
echo run ended
 
