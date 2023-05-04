#!/bin/bash
 
## job name 
#SBATCH --job-name=DOXG_threshold
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-12
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

## case options: SOG_NB or whidbey
case="main"
DO_thresh=2
# frame options: "FullDomain" or "Region" (for showing full domain or just region, in movie frame)
frame="FullDomain"

run_folders=(
"wqm_baseline"
"wqm_reference"
"4b"
"4c"
"4d"
"4e"
"4f"
"4g"
"4h"
"4i"
"4j"
"4k"
"4l"
)

file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
$case/DOXG/${run_folders[${SLURM_ARRAY_TASK_ID}]}/wc/daily_min_DOXG_wc.nc"
echo "Processing:" ${file_path}

script_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/\
SalishSeaModel-analysis/py_scripts/"

python ${script_path}plot_threshold_movie.py $case ${file_path} $DO_thresh $frame
