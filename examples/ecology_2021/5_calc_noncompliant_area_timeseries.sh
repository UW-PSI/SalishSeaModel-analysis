#!/bin/bash

#SBATCH --job-name=ncareats
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=0:30:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

$REPO_HOME/py_scripts/calc_noncompliant_area_timeseries.py -0.25 $CASE wqm_baseline
$REPO_HOME/py_scripts/calc_noncompliant_area_timeseries.py --no-parta -0.25 $CASE wqm_baseline
