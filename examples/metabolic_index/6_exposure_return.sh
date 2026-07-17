#!/bin/bash

#SBATCH --job-name=expreturn
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=40
#SBATCH --mem=25G
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

trap "kill 0" SIGINT # Ensure subprocesses are killed on interrupt

# Perform the exposure and return time calculations. These are parallelized.
$REPO_HOME/py_scripts/exposure_return_time.py $CASE 1 mi salmon routine
$REPO_HOME/py_scripts/exposure_return_time.py $CASE 1 mi crab routine
$REPO_HOME/py_scripts/exposure_return_time.py $CASE 1 mi sole routine

# Get aggregate exposure/return statistics for each species at appropriate
# depths.
$REPO_HOME/py_scripts/exposure_return_time_stats.py $CASE 1 mi salmon routine &
$REPO_HOME/py_scripts/exposure_return_time_stats.py $CASE 1 --depth=bt mi crab routine &
$REPO_HOME/py_scripts/exposure_return_time_stats.py $CASE 1 --depth=bt mi sole routine &
wait

# Make planar plots from shapefiles generated in previous step
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_max -tT "Salmon Max Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_exist_ExposureReturn_MI*_salmon-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_mean -tT "Salmon Mean Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_exist_ExposureReturn_MI*_salmon-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_max -tT "Crab Max Bottom Exposure - 2014 Conditions" -H 80 $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_crab-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_mean -tT "Crab Mean Bottom Exposure - 2014 Conditions" -H 80 $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_crab-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_max -tT "Sole Max Bottom Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_sole-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_mean -tT "Sole Mean Bottom Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_sole-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_max -tT "Salmon Max Net Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_exist_ExposureReturn_MI*_salmon-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_mean -tT "Salmon Mean Net Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_exist_ExposureReturn_MI*_salmon-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_sum -tT "Salmon Sum Net Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_exist_ExposureReturn_MI*_salmon-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_max -tT "Crab Max Bottom Net Exposure - 2014 Conditions" -H 80 $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_crab-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_mean -tT "Crab Mean Bottom Net Exposure - 2014 Conditions" -H 80 $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_crab-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_sum -tT "Crab Sum Bottom Net Exposure - 2014 Conditions" -H 80 $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_crab-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_max -tT "Sole Max Bottom Net Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_sole-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_mean -tT "Sole Mean Bottom Net Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_sole-lt-1.0.geojson
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_sum -tT "Sole Sum Bottom Net Exposure - 2014 Conditions" $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_bt_exist_ExposureReturn_MI*_sole-lt-1.0.geojson
