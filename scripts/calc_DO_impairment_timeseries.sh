#!/bin/bash
 
## job name 
#SBATCH --job-name=PercentImparied
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

## case options: SOG_NB or whidbey
case="SOG_NB"

run_folders=(
"1b_all_sog_wwtp_off" 
"1d_small_sog_wwtp_off" 
"2a_sog_river_0.5times" 
"wqm_baseline" 
"1c_all_sog_riv_off" 
"1e_med_sog_wwtp_off" 
"2b_sog_river_2times"
)

file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
$case/DOXG/${run_folders[${SLURM_ARRAY_TASK_ID}]}/daily_min_DOXG.nc"
echo "Processing:" ${file_path}
python calc_DO_impairment_timeseries.py $case ${file_path}
