#!/bin/bash
 
## job name 
#SBATCH --job-name=DOXG_netcdf
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-7
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

case="SOG_NB"
run_folders=(
"1b_all_sog_wwtp_off" 
"1d_small_sog_wwtp_off" 
"2a_sog_river_0.5times" 
"wqm_baseline" 
"wqm_reference"
"1c_all_sog_riv_off" 
"1e_med_sog_wwtp_off" 
"2b_sog_river_2times"
)

file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/\
${run_folders[${SLURM_ARRAY_TASK_ID}]}/ssm_output.nc"


echo "Processing:" ${file_path}
echo "As " $case " run"
python process_netcdf.py ${file_path} "DOXG" $case "min" 1 0

# ## Calculating DO impaired days, volume, % volume
# scope=("benthic" "wc")
# scope_array=${scope[${SLURM_ARRAY_TASK_ID}]} 

# echo "Calculating DO volume days impaired for: " ${scope_array}
# python calc_DO_impairment.py $case $scope_array

# ## Calculating DO < threshold days, volume, % volume
# thresholds=(
# "DO_standard" 
# "2" 
# "5"
# )

# echo ${thresholds[${SLURM_ARRAY_TASK_ID}]}

# python calc_DO_below_threshold.py %case% ${thresholds[${SLURM_ARRAY_TASK_ID}]} ${scope[1]}
