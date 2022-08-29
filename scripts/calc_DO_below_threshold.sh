#!/bin/bash
 
## job name 
#SBATCH --job-name=DOXG_lt_threshold
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-2
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

thresholds=(
"DO_standard" 
"2" 
"5"
)

## case options: SOG_NB or whidbey
case="SOG_NB"

echo ${thresholds[${SLURM_ARRAY_TASK_ID}]}

python calc_DO_below_threshold.py $case ${thresholds[${SLURM_ARRAY_TASK_ID}]} "wc"
