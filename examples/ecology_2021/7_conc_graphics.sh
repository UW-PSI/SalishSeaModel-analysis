#!/bin/bash

#SBATCH --job-name=extract
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --time=0:30:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

trap "kill 0" SIGINT # Ensure subprocesses are killed on interrupt

# Lots more different outputs could be created, this is just one example
$REPO_HOME/py_scripts/plot_conc_graphics_for_movies.py -m  $CASE min wc wqm_baseline var DOXG &
$REPO_HOME/py_scripts/plot_conc_graphics_for_movies.py -md $CASE min wc wqm_baseline var DOXG &
wait
