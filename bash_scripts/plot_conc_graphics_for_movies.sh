#!/bin/bash
#SBATCH --job-name=conc_movie_graphics
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-12
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## This script takes ~25 minutes to create 361 daily graphics for a year-long movie

##~~~~~~~~~~ BEGIN USER INPUT ~~~~~~~~~~
## case options: SOG_NB,  whidbey, or main
case="main"

## frame: "FullDomain" or "Region"
frame="FullDomain"

## location: "wc" (water column), "bottom", "surface"	
## if "wc" then the stat (e.g. min) is taken both as a daily minimum
## and a minimum across depth levels; otherwise, it's just a 
## daily minimum
loc="surface"

## Uncomment one of the three options below
## ~~~ OPTION 1 ~~~
##param="DOXG"
##stat_type="min"

## ~~~ OPTION 2 ~~~
##param="salinity"
##stat_type="mean"

## ~~~ OPTION 2 ~~~
param="NO3"
stat_type="mean"

##~~~~~~~~~~ END USER INPUT ~~~~~~~~~~

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

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

elif [ $case == "whidbey" ]; then

   echo "whidbey case"

   run_folders=(
   "wqm_reference"
   "wqm_baseline"
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

   echo "Error: Specify either SOG_NB or whidbey as case"

fi

file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
$case/${param}/${run_folders[${SLURM_ARRAY_TASK_ID}]}/${loc}/daily_${stat_type}_${param}_${loc}.nc"
echo "Processing:" ${file_path}

python ../py_scripts/plot_conc_graphics_for_movies.py $case $param $stat_type $loc ${file_path} $frame

# The following call is for creating individual graphics for EOPS
#python ../py_scripts/plot_conc_graphics_for_EOPS.py $case $param $stat_type $loc ${file_path} $frame
