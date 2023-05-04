#!/bin/bash
 
## job name 
#SBATCH --job-name=process_netcdf
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-3
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

param="DOXG"
case="whidbey"
stat_type="min"

folder_names=(
   "exist"
   "4k"
   "3l"
   "3j"
   )

py_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts"

file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/SSM_model_output/\
${folder_names[${SLURM_ARRAY_TASK_ID}]}/hotstart_rdm.nc"

python ${py_path}/process_netcdf.py ${file_path} ${param} ${case} ${stat_type} 1 1 