#!/bin/bash
# Created by Rachael D. Mueller at the Puget Sound Institute, with funding from King County. 

## job name 
#SBATCH --job-name=NonCompliance
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
## case: 'SOG' (7 scenarios), 'whidbey' (12 scenarios), 'main', 'south', 'hood', or 'SJF'
## "array" specification above needs to be 0-6 for "SOG_NB" and 0-9 for "whidbey"
case="whidbey"

## frame: "FullDomain" or "Region"
frame="Region"

## Non-compliant
## -0.25 mg/l referenced on pp. 49 and 50 of Appendix F in Optimization Report
## https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf
noncompliant=-0.25
echo "non-compliant threshold: " $noncompliant

## Path to python scripts
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
   "3j"
   "3k"
   "3l"
   "3m"
   )

elif [ $case == "main" ]; then

   echo "main region case"
 
   run_folders=(
   "wqm_baseline"
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

   echo "Error: Specify either SOG_NB, whidbey or main as case"

fi

## Path to post-processed netcdf files
file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
$case/DOXG/${run_folders[${SLURM_ARRAY_TASK_ID}]}/wc/daily_min_DOXG_wc.nc"
echo "Processing:" ${file_path}

python ${script_path}plot_noncompliant_graphics4movie.py $noncompliant $case ${file_path} $frame
