#!/bin/bash

## job name 
#SBATCH --job-name=HypoxiaMovie
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-11
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load apptainer

## case options: SOG_NB(7 scenarios) or whidbey(10 scenarios)
## "array" specification above needs to be 0-6 for "SOG_NB" and 0-9 for "whidbey"
case="whidbey"
## frame is either "FullDomain" for full domain, or "Region" for regional zoom
frame="Region"

## The following folder names and tags need to match 
## those in ../etc/config....yaml file. 
## Reading directly from that file is on the list for 
## future upgrades.

if [ $case == "SOG_NB" ]; then

   echo "SOG_NB case"

   run_folders=(
   "1b_all_sog_wwtp_off"
   "1d_small_sog_wwtp_off"
   "2a_sog_river_0.5times"
   "wqm_baseline"
   "wqm_reference"
   "1e_med_sog_wwtp_off"
   "2b_sog_river_2times"
   )
   
   run_tags=(
   "1b"
   "1d"
   "2a"
   "baseline"
   "reference"
   "1e"
   "2b"
   )

elif [ $case == "whidbey" ]; then

   echo "whidbey case"

   run_folders=(
   "wqm_baseline"
   "wqm_reference"
   "3b"
   "3c"
   "3e"
   "3f"
   "3g"
   "3h"
   "3i"
   "3j"
   "3l"
   "3m"
   )

   run_tags=(
   "baseline"
   "reference"
   "3b"
   "3c"
   "3e"
   "3f"
   "3g"
   "3h"
   "3i"
   "3j"
   "3l"
   "3m"
   )

else

   echo "Error: Specify either SOG_NB or whidbey as case"

fi


run_folders=(	
"wqm_baseline"
"wqm_reference"
"3b"
"3c"
"3e"
"3f"
"3g"
"3h"
"3i"
"3m"
)

run_tags=(
"baseline"
"reference"
"3b"
"3c"
"3e"
"3f"
"3g"
"3h"
"3i"
"3m"
)

## input graphics directory
graphics_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics/${case}/DOXG/threshold/movies/${frame}/${run_folders[${SLURM_ARRAY_TASK_ID}]}/"

## output movie directory
output_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/movies/${case}/DOXG/${frame}/"

echo ${graphics_dir}
apptainer exec --bind ${graphics_dir} --bind ${output_dir} ~/ffmpeg.sif ffmpeg -start_number 6 -framerate 6 -i ${graphics_dir}${case}_${frame}_${run_tags[${SLURM_ARRAY_TASK_ID}]}_threshold_2_wc_%d.png -c:v libx264 -pix_fmt yuv420p -vcodec mpeg4 ${output_dir}${case}_${frame}_${run_folders[${SLURM_ARRAY_TASK_ID}]}_threshold_2_wc.mp4
