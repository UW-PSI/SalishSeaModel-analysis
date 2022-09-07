#!/bin/bash
 
## job name 
#SBATCH --job-name=DOXG_imparied
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-6
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

## case options: SOG_NB or whidbey
case="SOG_NB"

## Impairement
## -0.25 mg/l referenced on pp. 49 and 50 of Appendix F in Optimization Report
## https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf
impairment=-0.2
impaired_txt=m0p2
echo "impairment: " $impairment

run_tag=(
"1b"
"1d"
"2a"
"baseline" 
"1c"
"1e"
"2b"
)

file_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/\
SOG_NB/DOXG/spreadsheets/impairment/${impaired_txt}/\
SOG_NB_${run_tag[${SLURM_ARRAY_TASK_ID}]}_wc_impaired_${impaired_txt}_TS_byRegion.xlsx"
## Add path to baseline or "current day" run to include as a baseline line graph to scenario graphs
baseline_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/\
KingCounty/data/SOG_NB/DOXG/spreadsheets/\
impairment/${impaired_txt}/SOG_NB_baseline_wc_impaired_${impaired_txt}_TS_byRegion.xlsx"
echo "Plotting: " ${file_path}
python plot_impairment_timeseries.py $impairment $case ${file_path} ${baseline_path}
