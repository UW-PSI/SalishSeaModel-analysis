#!/bin/bash

#SBATCH --job-name=ssm_do_extract

##SBATCH --mail-user=rdmseas@uw.edu
##SBATCH --mail-type=BEGIN
##SBATCH --mail-type=END
##SBATCH --mail-type=FAIL

#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=2:00:00
#SBATCH --mem=8G

module load stf/netcdf/c-ompi/4.8.1
# See https://github.com/conda/conda/issues/7980
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

export TMPDIR=~/scr

echo starting conversion
date
./ssm-analysis/rawcdf_extract.py -v --cache "$@"

date
echo conversion finished
