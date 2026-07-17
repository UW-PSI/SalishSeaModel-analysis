#!/bin/bash

#SBATCH --job-name=dosat
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=25G
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

$REPO_HOME/py_scripts/DO_Saturation.py $CASE
