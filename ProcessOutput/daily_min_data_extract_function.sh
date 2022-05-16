#!/bin/bash
 
## job name 
#SBATCH --job-name=BS_2st
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

python daily_min_data_extract_function.py 'DO' '/mmfs1/home/rdmseas/projects/ssmc/rachael-ssmc/output/daily_min'

date
echo run ended
 
