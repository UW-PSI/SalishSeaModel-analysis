#!/bin/bash
# Created by Rachael D. Mueller at the Puget Sound Institute, with funding from King County.
# The Main Region case had to be run differently for the baseline and reference runs
# For these runs, the graphics are named with run_tag vs. run_folder (as was/is used for the other scenarios)
# the graphic name after "-i" needs to include run_tag rather than run_folder for the baseline and reference runs only

## job name 
#SBATCH --job-name=%Hypoxic
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
module load apptainer

## case options: SOG_NB or whidbey
## "array" specification above needs to be 0-6 for "SOG_NB" and 0-9 for "whidbey"
case="whidbey"

## frame: "FullDomain" or "Region"
frame="Region"

## DOthresh: Threshold used to define hypoxic
DOthresh=2


## Output movie directory
output_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/movies/${case}/DOXG/percent_hypoxic/${frame}/"

## ------------  END USER INPUT -------------------
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
   "3k"
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
   "3k"
   "3l"
   "3m"
   )

elif [ $case == "main" ]; then

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

    run_tags=(
    "baseline"
    "reference"
    "M.tp1"
    "M.tp2"
    "M.tp3"
    "M.tp4"
    "M.tp5"
    "M.tp6"
    "M.tp7"
    "M.tp8"
    "M.tp9"
    "M.r1"
    "M.r2"
    )

else

   echo "Error: Specify either SOG_NB, whidbey, or main as case"

fi

## Input graphics directory
graphics_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics/${case}/DOXG/percent_hypoxic/movies/${frame}/${run_folders[${SLURM_ARRAY_TASK_ID}]}/"

echo "Saving output to: " ${output_dir}

apptainer exec --bind ${graphics_dir} --bind ${output_dir} ~/ffmpeg.sif ffmpeg -start_number 6 -framerate 6 -i ${graphics_dir}${case}_${run_tags[${SLURM_ARRAY_TASK_ID}]}_percentDO_lt_${DOthresh}_wc_%d.png -c:v libx264 -pix_fmt yuv420p -vcodec mpeg4 ${output_dir}${case}_${run_tags[${SLURM_ARRAY_TASK_ID}]}_percentDO_lt_${DOthresh}_${frame}.mp4
