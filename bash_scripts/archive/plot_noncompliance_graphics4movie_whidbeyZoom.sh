#!/bin/bash
 
## job name 
#SBATCH --job-name=NonCompliance
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-10
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

## case options: SOG_NB(7 scenarios) or whidbey(10 scenarios)
## "array" specification above needs to be 0-6 for "SOG_NB" and 0-9 for "whidbey"
case="whidbey"

## Non-compliance
## -0.25 mg/l referenced on pp. 49 and 50 of Appendix F in Optimization Report
## https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf
noncompliant=-0.25
echo "noncompliance threshold: " $noncompliant


## Path to python script used here
script_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/\
SalishSeaModel-analysis/py_scripts/"

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
   "3l"
   "3m"
   )

else

   echo "Error: Specify either SOG_NB or whidbey as case"

fi

## Paths to post-processed netcdf files
file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
$case/DOXG/${run_folders[${SLURM_ARRAY_TASK_ID}]}/wc/daily_min_DOXG_wc.nc"
echo "Processing:" ${file_path}

python ${script_path}plot_noncompliant_graphics4movie_whidbeyZoom.py $noncompliant $case ${file_path}
