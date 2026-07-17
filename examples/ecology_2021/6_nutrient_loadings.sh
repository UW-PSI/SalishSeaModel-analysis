#!/bin/bash

#SBATCH --job-name=table1nl
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=0:30:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

mkdir -p reports/
$REPO_HOME/py_scripts/calc_nutrient_loadings.py $CASE reports/Table1_NutrientLoadings_${CASENAME}_DIN.xlsx
