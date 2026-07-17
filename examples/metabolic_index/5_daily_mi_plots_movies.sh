#!/bin/bash

#SBATCH --job-name=movies
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=20
#SBATCH --mem=25G
#SBATCH --time=0:40:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

trap "kill 0" SIGINT # Ensure subprocesses are killed on interrupt

# -t: Use toner color scheme rather than default terrain
# -m: Invoke ffmpeg at end
# -d: Make a delta plot (subtract reference)
$REPO_HOME/py_scripts/plot_conc_graphics_for_movies.py -tm  $CASE min wc exist mi salmon routine &
$REPO_HOME/py_scripts/plot_conc_graphics_for_movies.py -tmd $CASE min wc exist mi salmon routine &
for species in sole crab; do
  $REPO_HOME/py_scripts/plot_conc_graphics_for_movies.py -tm  $CASE min bt exist mi $species routine &
  $REPO_HOME/py_scripts/plot_conc_graphics_for_movies.py -tmd $CASE min bt exist mi $species routine &
done
wait
