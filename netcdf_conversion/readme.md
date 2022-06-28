---
# Instructions for sub-sampling the v4-like netcdf output created by Bens' C++ script 
---

The shell script `do_extract_klone.sh` is modified from a version provided by Ben Roberts (06/16/2022).
This file described the changes made and an overview of running the code.

### Environment setup
This shell script relies on a `miniconda3` environment.  I used my existing environment for my Jupyter notebooks.  
For background/setup, see my instructions on [installing miniconda3 on Hyak](https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/docs/HyakOnboarding.md#install-miniconda3-in-lab-workspace) 
and [setting up klone_jupyter from yaml file](https://github.com/RachaelDMueller/KingCounty-Rachael/blob/main/docs/HyakOnboarding.md#create-a-miniconda-environment-using-a-yaml-file)

### Modifying the shell script
There are two parts of the shell script that will need to be modified to fit the user's setup
1. miniconda3 environment.  
  
  The two lines in this shell script that rely on the `miniconda3` setup are:
  ```
  source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
  conda activate klone_jupyter
  ```
  These lines will need to be modified to reflect the user's `miniconda3` environment. 

3. path to `rawcdf_extract.py`.

The path to `rawcdf_extract.py` will also need to be modified to reflect the relative path of `ssm-analysis` to the location of the shell script
```
../../ssm-analysis/rawcdf_extract.py -v --cache "$@"
```
### Running the shell script
From Ben's email:
```
$ ./rawcdf_extract.py --help
usage: rawcdf_extract.py [-h] [-d DOMAIN_NODE_SHAPEFILES]
                        [-m MASKED_NODES_FILE] [--invar INPUT_VARS] [-v]
                        [-c CHUNK_SIZE] [--cache]
                        incdf [incdf ...] outcdf outprefix

Extract data from SSM netcdf output files

positional arguments:
 incdf                 each input CDF file
 outcdf                the output CDF file (created if it doesn't exist)
 outprefix             a prefix for the extracted variables in the output CDF

optional arguments:
 -h, --help            show this help message and exit
 -d DOMAIN_NODE_SHAPEFILES
                       Specify a domain node shapefile
 -m MASKED_NODES_FILE  Specify a different masked nodes text file
 --invar INPUT_VARS    Extract the values of a different output variable
 -v, --verbose         Print progress messages during the extraction
 -c CHUNK_SIZE, --chunk-size CHUNK_SIZE
                       Process this many CDF files at once
 --cache               Use a read/write cache in a temporary directory


Performance of this script suffers greatly if you run it on Hyak
without using the --cache option.

The variable names correspond to what's in the input netCDF file, for
instance 'DOXG' is dissolved oxygen. Each one needs an extra specifier
for what depth layers you want, following a colon. Right now the only
choices are "bottom" (take the bottom layer only) and "all".

Data is extracted only for nodes that are contained within the domain
shapefile, but you can specify a different shapefile (that you would
have built using ProcessGrid.ipynb).

```
The location of the `netcdf` output by Su Kyong for output from Ben's C++ script provided is `/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_baseline/ssm_output.nc`
I tested the script using 
```
sbatch do_extract_klone.sh '/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_baseline/ssm_output.nc' 'test.nc' 'ALL'
```
### Resulting netcdf
The resulting `test.nc` has the following metatdata:
```
(base) [rdmseas@klone1 KingCounty]$ ncdump -h test.nc
netcdf test {
dimensions:
	time = 8784 ;
	node = 4446 ;
variables:
	int node(node) ;
	float time(time) ;
	float ALLDOXG_bottom(time, node) ;
}
```
which indicates that bottom DO was extracted for all nodes...?
