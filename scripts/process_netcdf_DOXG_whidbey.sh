#!/bin/bash
 
## job name 
#SBATCH --job-name=whidbey_netcdf
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-6
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
"3c"
"3g"
"3h"
"3i"
)

## Processing output files to smaller-sized netcdfs
file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/\
${run_folders[${SLURM_ARRAY_TASK_ID}]}/ssm_output.nc"	

echo ${file_path}
python process_netcdf.py ${file_path} "DOXG" case "min" 1 0

## Calculating DO impaired days, volume, % volume
scope=("benthic" "wc")

echo "Calculating DO volume days impaired for: " ${scope}
python calc_DO_impairment.py case ${scope[${SLURM_ARRAY_TASK_ID}]%2} 

## Calculating DO < threshold days, volume, % volume
thresholds=(
"DO_standard" 
"2" 
"5"
)

echo ${thresholds[${SLURM_ARRAY_TASK_ID}]}

python calc_DO_below_threshold.py case ${thresholds[${SLURM_ARRAY_TASK_ID}]%3} "wc"