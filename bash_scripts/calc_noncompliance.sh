#!/bin/bash
# Created by Rachael D. Mueller at the Puget Sound Institute, with funding from King County.

## job name 
#SBATCH --job-name=DOXG_imparied
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-1
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

scope=("benthic" "wc")

## case options: SOG_NB, whidbey, or Main
case="main"

## Impairement
## -0.25 mg/l referenced on pp. 49 and 50 of Appendix F in Optimization Report
## https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf
noncompliant=-0.25
echo "noncompliance threshold: " $noncompliant

echo "Calculating DO volume days non-compliant for: " ${scope[${SLURM_ARRAY_TASK_ID}]}
python /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/calc_noncompliance.py $case $noncompliant ${scope[${SLURM_ARRAY_TASK_ID}]} 
