#!/bin/bash
# Created by Rachael D. Mueller at the Puget Sound Institute, with funding from King County.

## job name 
#SBATCH --job-name=5panel_noncompliant
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

## case options: SOG_NB or whidbey
case="whidbey"

## Noncompliant
## -0.25 mg/l referenced on pp. 49 and 50 of Appendix F in Optimization Report
## https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf
noncompliant=-0.25
noncompliant_txt=m0p25
echo "noncompliant: " $noncompliant

xlxs_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
${case}/spreadsheets/"

## Add path to baseline or "current day" run to include as a baseline line graph to scenario graphs
baseline_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/\
KingCounty/data/${case}/spreadsheets/${case}_baseline_wc_noncompliant_${noncompliant_txt}_TS_byRegion.xlsx"

script_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"

python ${script_path}plot_5panel_noncompliant_timeseries.py $noncompliant $case ${xlxs_dir} ${baseline_path}
