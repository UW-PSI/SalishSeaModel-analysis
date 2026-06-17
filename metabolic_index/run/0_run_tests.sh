#!/bin/bash

#SBATCH --job-name=runtests
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=0:10:00
##SBATCH --mail-user=YOUR_EMAIL_HERE

# Make sure to change these paths to represent your setup
source $HOME/miniforge3/etc/profile.d/conda.sh
export MAMBA_ROOT_PREFIX=$GSC_HOME/miniforge3
source $HOME/miniforge3/etc/profile.d/mamba.sh

conda activate psi_mi

python -m unittest discover -s ../tests
