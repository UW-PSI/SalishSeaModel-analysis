#!/bin/bash

#SBATCH --job-name=tables
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --mem=25G
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

trap "kill 0" SIGINT # Ensure subprocesses are killed on interrupt

# Calculate all the statistics for MI below 1 for each
# species. We're only interested in routine in this study.
$REPO_HOME/py_scripts/calc_below_threshold.py            $CASE 1 mi salmon routine &
$REPO_HOME/py_scripts/calc_below_threshold.py --depth=bt $CASE 1 mi salmon routine &
$REPO_HOME/py_scripts/calc_below_threshold.py --depth=bt $CASE 1 mi crab routine &
$REPO_HOME/py_scripts/calc_below_threshold.py --depth=bt $CASE 1 mi sole routine &
wait

# Make time series plots of all the threshold daily data
# Daily volumes for 3D thresholds
$REPO_HOME/py_scripts/plot_daily_volumes_simple.py -b 4.3 -y 0.45 $CASE SSM_output/spreadsheets/calc_below_threshold/${CASENAME}_MIroutine_*-lt-1.0.xlsx &
# Daily areas for bottom-only
$REPO_HOME/py_scripts/plot_daily_volumes_simple.py -a -b 166 -y 51 $CASE SSM_output/spreadsheets/calc_below_threshold/${CASENAME}_bt_MIroutine_*-lt-1.0.xlsx &

# Make planar plots for MI<1
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_MI*_salmon-lt-1.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist -d $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_MI*_salmon-lt-1.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_bt_MI*_salmon-lt-1.0.geojson &
wait
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist -d $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_bt_MI*_salmon-lt-1.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist -H 80 $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_bt_MI*_crab-lt-1.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist -H 80 -d $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_bt_MI*_crab-lt-1.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist -H 100 $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_bt_MI*_sole-lt-1.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -tc exist -H 100 -d $CASE SSM_output/shapefiles/calc_below_threshold/${CASENAME}_bt_MI*_sole-lt-1.0.geojson &
wait
