#!/bin/bash

#SBATCH --job-name=DOexp
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=20
#SBATCH --time=0:10:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

trap "kill 0" SIGINT # Ensure subprocesses are killed on interrupt

$REPO_HOME/py_scripts/exposure_return_time.py $CASE 2 var DOXG
$REPO_HOME/py_scripts/exposure_return_time.py $CASE 5 var DOXG

$REPO_HOME/py_scripts/exposure_return_time_stats.py $CASE 2 var DOXG &
$REPO_HOME/py_scripts/exposure_return_time_stats.py $CASE 5 var DOXG &
wait

# Make planar plots from shapefiles generated in previous step
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_max -T 'Max DO<2 exposure - Baseline' $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-2.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_mean -T 'Mean DO<2 exposure - Baseline' $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-2.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_max -T 'Max DO<2 net exposure - Baseline' $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-2.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_mean -T 'Mean DO<2 net exposure - Baseline' $CASE SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-2.0.geojson &
wait
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_max $CASE -T 'Max DO<5 exposure - Baseline' SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-5.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c exp_mean $CASE -T 'Mean DO<5 exposure - Baseline' SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-5.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_max $CASE -T 'Max DO<5 net exposure - Baseline' SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-5.0.geojson &
$REPO_HOME/py_scripts/plot_planar_days_below_threshold.py -c netexp_mean $CASE -T 'Mean DO<5 net exposure - Baseline' SSM_output/shapefiles/ExposureReturn/${CASENAME}_wqm_baseline_ExposureReturn_DOXG-lt-5.0.geojson &
wait
