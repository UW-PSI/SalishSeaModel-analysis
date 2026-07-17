#!/bin/bash

#SBATCH --job-name=noncompl
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=0:30:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

$REPO_HOME/py_scripts/calc_noncompliance.py $CASE -0.25 wc
$REPO_HOME/py_scripts/calc_noncompliance.py --no-parta $CASE -0.25 wc
