#!/bin/bash

#SBATCH --job-name=runtests
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=0:10:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

source paths.rc

python -m unittest discover -s $REPO_HOME/tests
