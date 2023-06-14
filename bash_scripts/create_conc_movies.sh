#!/bin/bash
# Created by Rachael D. Mueller at the Puget Sound Institute, with funding from King County.

## job name 
#SBATCH --job-name=conc_movies
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
case="main"

## location: "wc" (water column), "bottom", "surface"   
## if "wc" then the stat (e.g. min) is taken both as a daily minimum
## and a minimum across depth levels; otherwise, it's just a 
## daily minimum
loc="surface"

## frame: "FullDomain" or "Region"
frame="Region"

## Uncomment one of the three options below
## ~~~ OPTION 1 ~~~
##param="salinity"
##stat_type="mean"

## ~~~ OPTION 2 ~~~
param="NO3"
stat_type="mean"

## ~~~ OPTION 3 ~~~
##param="DOXG"
##stat_type="min"

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

   echo "main region case"

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

else

   echo "Error: Specify either SOG_NB, whidbey, or main as case"
   
fi

graphics_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics/${case}/${param}/concentration/movies/${frame}/${loc}/${run_folders[${SLURM_ARRAY_TASK_ID}]}/"

output_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/movies/${case}/${param}/concentration/${frame}/"

echo ${graphics_dir}

apptainer exec --bind ${graphics_dir} --bind ${output_dir} ~/ffmpeg.sif ffmpeg -start_number 6 -framerate 6 -i ${graphics_dir}${case}_${run_folders[${SLURM_ARRAY_TASK_ID}]}_${param}_${stat_type}_conc_${loc}_%d.png  -vcodec mpeg4 ${output_dir}${case}_${run_folders[${SLURM_ARRAY_TASK_ID}]}_${param}_${stat_type}_${loc}_${frame}.mp4
