#!/bin/bash

#SBATCH --job-name=DOthresh
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=0:30:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

trap "kill 0" SIGINT # Ensure subprocesses are killed on interrupt

$REPO_HOME/py_scripts/calc_below_threshold.py $CASE 2 var DOXG &
$REPO_HOME/py_scripts/calc_below_threshold.py $CASE 5 var DOXG &
wait

# Now make plots based on this data
for f in SSM_output/spreadsheets/calc_below_threshold/${CASENAME}_DOXG-lt-*.xlsx; do
  $REPO_HOME/py_scripts/plot_daily_volumes_simple.py $CASE $f &
done
wait
$REPO_HOME/py_scripts/plot_multi_threshold_stacked_volumes.py $CASE
for f in SSM_output/shapefiles/calc_below_threshold/${CASENAME}_DOXG-lt-*.geojson; do
  $REPO_HOME/py_scripts/plot_planar_days_below_threshold.py $CASE $f &
  $REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -d $CASE $f &
done
wait
