#!/bin/bash
## job name 
#SBATCH --job-name=inlet_nc
#SBATCH --account=ssmc
#SBATCH --partition=compute
#SBATCH --nodes=1       
#SBATCH --ntasks-per-node=1
#SBATCH --array=0-4
#SBATCH --time=0:30:00 
#SBATCH --mem=175G 
#SBATCH --mail-user=rdmseas@uw.edu

## Modules needed to run
module purge
module load foster/python/miniconda/3.8
source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
conda activate klone_jupyter

##~~~~~~~~~~ BEGIN USER INPUT ~~~~~~~~~~
nc_file="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/SSM_model_output/NPP_workshop120622_WQM_sm.nc"
shp_file="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-grid/shapefiles/SSMGrid2_tce_ecy_node_info_v2_10102022_inlets/SSMGrid2_tce_ecy_node_info_v2_10102022_inlets.shp"
output_netcdf_dir="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/NPP_workshop_120622"
param=(
"salinity"
"DOXG"
"B1"
"B2"
"NO3"
)
stat_type="median"
inlet="Bellingham Bay"

echo "running python script"

python create_2Dmedian_inlet_netcdf.py $nc_file $shp_file $output_netcdf_dir ${param[${SLURM_ARRAY_TASK_ID}]} $stat_type $inlet

