#!/bin/bash
 
## job name 
#SBATCH --job-name=whidbey_netcdf
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-9
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

case="whidbey"

run_folders=(	
"wqm_baseline"
"wqm_reference"
"3b"
"3e"
"3f"
"3g"
"3h"
"3i"
"3l"
"3m"
)


## Processing output files to smaller-sized netcdfs
file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/\
${run_folders[${SLURM_ARRAY_TASK_ID}]}/ssm_output.nc"

echo "Processing:" ${file_path}
echo "As " $case " run"
python /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/process_netcdf.py ${file_path} "DOXG" $case "min" 1 0

## Calculating DO impaired days, volume, % volume
## scope=("benthic" "wc")

## echo "Calculating DO volume days impaired for: " ${scope}

## python /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/calc_DO_impairment.py $case $impairment ${scope[${SLURM_ARRAY_TASK_ID}]} 
