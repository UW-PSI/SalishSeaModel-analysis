#!/bin/bash
# Created by Rachael D. Mueller at the Puget Sound Institute, with funding from King County.

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

## case options: SOG_NB or whidbey
## "array" specification above needs to be 0-6 for "SOG_NB" or 0-9 for "whidbey" 
case="whidbey"

## Non-compliance
## -0.25 mg/l referenced on pp. 49 and 50 of Appendix F in Optimization Report
## https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf
noncompliance=-0.25
noncompliant_txt=m0p25
echo "noncompliance threshold: " $noncompliance

## Path to script used in this file
script_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"
echo "Plotting: " ${file_path}

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
   run_tag=(
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
   "3l"
   "3m"
   )
   run_tag=(
   "baseline"
   "reference"
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
## Excel spreadsheet file paths
file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
${case}/spreadsheets/${case}_${run_tag[${SLURM_ARRAY_TASK_ID}]}_wc_noncompliant_${noncompliant_txt}_TS_byRegion.xlsx"

## Path to "Current conditions" run to include in graphics for comparison
## Add path to baseline or "current day" run to include as a baseline line graph to scenario graphs
baseline_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/\
KingCounty/data/${case}/spreadsheets/${case}_baseline_wc_noncompliant_${noncompliant_txt}_TS_byRegion.xlsx"


python ${script_path}plot_noncompliance_timeseries.py $noncompliance $case ${file_path} ${baseline_path} "False"
