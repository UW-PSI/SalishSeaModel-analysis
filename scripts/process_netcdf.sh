#!/bin/bash
 
## job name 
#SBATCH --job-name=SSM_netcdf
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=7       
#SBATCH --ntasks-per-node=1
#SBATCH --time=5:00:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

echo  starting the run
date

python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_baseline/ssm_output.nc" &
python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1b_all_sog_wwtp_off/ssm_output.nc" &
python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1c_all_sog_riv_off/ssm_output.nc" &
python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1d_small_sog_wwtp_off/ssm_output.nc" &
python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1e_med_sog_wwtp_off/ssm_output.nc" &
python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/2a_sog_river_0.5times/ssm_output.nc" &
python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/2b_sog_river_2times/ssm_output.nc" &

date
echo run ended

