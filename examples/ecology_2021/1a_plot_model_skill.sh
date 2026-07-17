#!/bin/bash

#SBATCH --job-name=modelskill
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
# Script is very slow on outputs in multi-file datasets, I timed it at nearly 40 minutes
#SBATCH --time=0:10:00
#SBATCH --mem=20G
##SBATCH --mail-user=YOUR_EMAIL_HERE

GSC_HOME=/gscratch/ssmc/USRS/PSI/Ben
REPO_HOME=$GSC_HOME/SalishSeaModel-analysis_2026update
CASE=SSM_config_ecy21.yaml

# Make sure to change these paths to represent your setup
source $GSC_HOME/miniforge3/etc/profile.d/conda.sh
export MAMBA_ROOT_PREFIX=$GSC_HOME/miniforge3
source $GSC_HOME/miniforge3/etc/profile.d/mamba.sh

conda activate psi_ssm

$REPO_HOME/py_scripts/plot_model_skill.py $CASE
