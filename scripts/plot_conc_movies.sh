#!/bin/bash
 
## job name 
#SBATCH --job-name=DOXG_imparied
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
param="NO3"
stat_type="mean"
loc="surface"

##param="NO3"
##stat_type="max"

##param="DOXG"
##stat_type="min"

run_folders=(
"1b_all_sog_wwtp_off" 
"1d_small_sog_wwtp_off"
"2a_sog_river_0.5times"
"wqm_baseline"
"wqm_reference"
"1e_med_sog_wwtp_off" 
"2b_sog_river_2times"
)

file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
$case/${param}/${run_folders[${SLURM_ARRAY_TASK_ID}]}/${loc}/daily_${stat_type}_${param}_${loc}.nc"
echo "Processing:" ${file_path}
python plot_conc_movies.py $case $param $stat_type $loc ${file_path} 
