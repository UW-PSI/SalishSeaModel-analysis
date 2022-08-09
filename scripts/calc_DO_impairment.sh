#!/bin/bash
 
## job name 
#SBATCH --job-name=DOXG_imparied
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

scope=("benthic" "wc")
case="whidbey"

echo "Calculating DO volume days impaired for: " ${scope}
python calc_DO_impairment.py case ${scope[${SLURM_ARRAY_TASK_ID}]} 
