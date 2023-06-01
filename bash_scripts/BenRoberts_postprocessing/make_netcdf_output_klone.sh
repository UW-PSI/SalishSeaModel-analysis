#!/bin/sh

## job name 
#SBATCH --job-name=ssmhist2cdf

#SBATCH --mail-user=rdmseas@uw.edu   # email address
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL

#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=175G
#SBATCH --time=2:00:00

# Modules needed to run
module purge
module load stf/netcdf/c-ompi/4.8.1
module unload ompi/4.1.1
module load ompi/4.1.3

RUNID="4c"

export PATH="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/bash_scripts/BenRoberts_postprocessing:$PATH"

CONFIG="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/bash_scripts/BenRoberts_postprocessing/history_npp_wksp120622_sm_A8.yml"
OUTFILE="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/${RUNID}/ssm_hotstart_${RUNID}.nc"
SSM_PATH="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel/${RUNID}/hotstart/outputs"

rm -f "$OUTFILE"
echo ${SSM_PATH}
time mpirun -np $SLURM_NTASKS ssmhist2cdf -v --last-is-bottom -c $CONFIG \
	"$OUTFILE" ${SSM_PATH}/ssm_history_*.out
