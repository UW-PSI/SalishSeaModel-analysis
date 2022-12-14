# General
**UW Technology  Help**
Any questions on hardware or software from UW can be directed to: 
**Email**: tachelp@uw.edu 
**Phone**: 253-692-4357 
[Chat and website](https://www.tacoma.uw.edu/it)

# New runs
- Existing (replicate run as proof of concept)
- 3j (move shallow loading to deep) as proof of concept for creating input file, running model and doing QAQC
### Notes from Su Kyong
These step-by-step instructions were prepared based on the scenario runs conducted by SSMC in collaboration with PSI during June-September in 2022. The models used for these scenarios are FVCOM_v2.7ecy (HYD) and FVCOM_ICM_v2 (WQM). 
If you have any questions, please contact Su Kyong Yun at her new work address at sukyong.yun@pnnl.gov
1. Setting up Input Files
   1. All information and files needed for setting up input files is located in the ‘input_setting’ folder
   2. Total of 7 files are needed to set up the input files (Table 1).  No need to update the first four, only the remiaining 3, `run_strategy` and `main*`
      1. create_scenario_pnt_wq_v3_090622.py
      2. exist_ref_diff_N-conc.xlsx
      3. ssm_pnt_wq_header.txt
      4. ssm_pnt_wq_exist.dat
      5. run_strategy.xlsx
      6.  main_create_scenario_pnt_wq.py
      7.  main_create_scenario_pnt_wq.sh
2. Running the model.`wqm_default` folder contains all needed files
   1. run the `coldstart_setup.sh`
      1. change working directory to the directory where you want to create the scenario list. wrk_dir=`/mmfs1/gscratch/ssmc/GRPS/ssmc_dev/SuKyong/KingCounty/retrial/`
      2. change scenario id (e.g. `4c`)
      3. change directory where `wqm_default/coldstart` is located
         1. `cp -R /mmfs1/gscratch/ssmc/GRPS/ssmc_dev/SuKyong/KingCounty/PSI/wqm_default/coldstart $wrk_dir_temp`
      4. change directory where scenario `ssm_pnt_wq.dat` is located
         1. `cp
/mmfs1/gscratch/ssmc/GRPS/ssmc_dev/SuKyong/KingCounty/PSI/input_settin g/ssm_pnt_wq_$scenario_index.dat $wrk_dir_temp/coldstart/inputs/ssm_pnt_wq.dat`
   2. run the `hotstart_setup.sh`
       1. change working directory to the directory that you want to create scenario list, wrk_dir=`/mmfs1/gscratch/ssmc/GRPS/ssmc_dev/SuKyong/KingCounty/retrial/`
       2. change scenario id (e.g. `4c`)
       3. change directory where `wqm_default/hotstart` is located
          1. `cp -R /mmfs1/gscratch/ssmc/GRPS/ssmc_dev/SuKyong/KingCounty/PSI/wqm_defaul t/hotstart $wrk_dir_temp`
       4. change directory where scenario `ssm_pnt_wq.dat` is located 
          1. `cp
/mmfs1/gscratch/ssmc/GRPS/ssmc_dev/SuKyong/KingCounty/PSI/input_settin g/ssm_pnt_wq_$scenario_index.dat $wrk_dir_temp/hotstart/inputs/ssm_pnt_wq.dat`


# HYAK setup
Reccommended solution by Ryan McGregor:

1) Set your .condarc and .bashrc file to use /tmp as your package cache directory. This avoids the annoying quota exceeded being triggered due to the cache that conda builds.

```
ryanmcgr@klone1 § /gscratch/hyakteam/ryanmcgr/test_conda_dir § vim ~/.condarc
  envs_dirs:
    - $CONDA_WORKING_DIR/envs
  pkgs_dirs:
    - $CONDA_WORKING_DIR/pkgs

 ryanmcgr@klone1 § /gscratch/hyakteam/ryanmcgr/test_conda_dir § cat .bashrc
  export CONDA_WORKING_DIR=/tmp/ryanmcgr_conda  
```
2) When building the conda environment, override the path that conda places the environment at using the -p flag.  
 ryanmcgr@klone1 § /gscratch/hyakteam/ryanmcgr/test_conda_dir § conda env create -f ./klone-jupyter.yml -p ./conda_test_env

From Matt:

One option is to tell miniconda to use a specific directory for libraries and such -- this can be done via either the .condarc file or via environment variable -- see details here:
https://docs.conda.io/projects/conda/en/latest/user-guide/configuration/use-condarc.html#specify-env-directories

The symlink solution is also viable -- the command format is 
```
ln -s <target> <symlink name>
```
 (which does intuitively seem backwards, but is in fact the way the command works) -- I think where you had the problem may have been use of the $HOME environment variable, which may have been point somewhere else --  the following will work (if you remove ~/.conda first):

```
ln -s /mmfs1/home/rdmseas/.conda  /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda
```
### Install of seawater package
Seawater package was cloned from [Bjorn's Git repo](https://github.com/bjornaa/seawater) and placed in `/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty`

Do the following to use this package (as I don't yet have path permanently added):
```
sys.path.insert(1, '/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/seawater')
from seawater import dens
```

# Sediment and NPP netcdf
### Message written to Ben
I'm digging back into creating a netcdf using your yaml file technique and need to add "settling rate" variables. I'm seeing:
```
! WSLBNET,  & !net settling rate of LPOM (m/d)
! WSRBNET,  & !net settling rate of RPOM (m/d)
```
but neither of these are in the output lines of `wqm_main.F`. My notes have line `2784` of `wqm_main.F` reflecting output for layers 1-10 and line `2824` showing addition outputs for 10-only (additional to those output from line `2784)`. I have these variables listed with notes and see values of m2/day associated with, e.g., `JHS_GL`. Line `2652` shows: `JHS_GL = JHSTM1S`. `JHSTM1S` is "grepped" in `mod_sed.F` as being related to "!dissolved Si flux to water column (gO2/m^2/d)", so I think this variable is a flux to the water rather than a settling rate. The other variable that I'm seeing with at unit that reflects a rate is `JPON`.

```
./mod_sav.F:  !SEDPONSAV (gN/m^2/day) --> JPON (mgN/m^2/day) -> PON1, PON2, PON3 (source of particulate organic nitrogen in sediments)
./mod_sav.F:  !SEDPOPSAV (gP/m^2/day) --> JPON (mgP/m^2/day) -> POP1, POP2, POP3 (source of particulate organic phosphorus in sediments)
```
I'm just a bit unfamiliar with terms here. I would interpret the above to combine settling rate (m/day) and concentration (g/m3) => i.e. a flux....so I'm a bit at a loss for finding a settling rate.

When I grep all the files for "settling rate," I see them in `mod_sed` and `mod_wqm`  
```
./mod_sed.F:    !******* Assign base net settling rates
./mod_sed.F:                  WSSNET (B) = WSSNET (B) + WSSSAV * SAVEFCT !increase of settling rate (m/d) to suspended solids
./mod_sed.F:                  WSLNET (B) = WSLNET (B) + WSLSAV * SAVEFCT !increase of settling rate (m/d) to LPOM
./mod_sed.F:                  WSRNET (B) = WSRNET (B) + WSRSAV * SAVEFCT !increase of settling rate (m/d) to RPOM
./mod_sed.F:                  WS1NET (B) = WS1NET (B) + WS1SAV * SAVEFCT !increase of settling rate (m/d) to alg 1
./mod_sed.F:                  WS2NET (B) = WS2NET (B) + WS2SAV * SAVEFCT !increase of settling rate (m/d) to alg 2
./mod_sed.F:                  WS3NET (B) = WS3NET (B) + WS3SAV * SAVEFCT !increase of settling rate (m/d) to alg 3
./mod_sed.F:                  WSUNET (B) = WSUNET (B) + WSUSAV * SAVEFCT !increase of settling rate (m/d) to particulate biogenic silicate (unavaiable)
./mod_wqm.F:  !Water column settling rates
./mod_wqm.F:     & WS2, WS3, WSU, WSSHI !fixed solids settling rate (m/day) when solids concentration is high
./mod_wqm.F:     & WS1NET, WS2NET, WS3NET, WSUNET !settling rate of particulate biogenic (unavaiable) silica (m/d)
```
Does all of the above mean that these variables don't exist in the output and that I'd need to add them to the write out function in order for us to use them?

### Notes on variables in file(s)

**Removed**
- h
- zeta
- NO3
- NH4

**Included**
- B1 [6]: Algal group 1 (diatoms according to Ben in email 8/29/22. Confirmed as `G1` in [this reference](https://apps.ecology.wa.gov/publications/documents/1703010.pdf))
- B2 [7]: Algal group 2 (dinoflagellates, in same email)
- NetPP [11]:total net primary production
- JPOC1-3 [46-48]: sed particulate organic carbon
- JPON1-3 [49-51]: sed particulate organic nitrogen
- JPOP1-3 [52-54]: sed particulate organic phosphate
- JPOS [55]: sed particulate organic silica

**General Information**
Su Kyong shared [this very useful resource on the Sediment Diagenesis Module](https://apps.ecology.wa.gov/publications/documents/1703010.pdf). 

**Sediment Diageneis**
<blockquote>
Internal sediment state variables for diagenesis are based on the multi-class G model, in which the organic forms are divided based on their reactivity into reactive (G1), refractory (G2), and inert (G3) forms (Figure A-1). Therefore, the fluxes of particulate organic carbon (oxygen equivalents), nitrogen, and phosphorus are subdivided into G-class fractions, based on user specified ratios. Due to the negligible thickness of the upper layer, deposition (as described later) is assumed to proceed directly from the water column to the lower (anoxic) sediment layer.
</blockquote>

and 
- POC1 = G1 particulate organic carbon in layer 2 (mgO2/L)
- POC2 = G2 particulate organic carbon in layer 2 (mgO2/L)
- POC3 = G3 particulate organic carbon in layer 2 (mgO2/L)
- PON1 = G1 particulate organic nitrogen in layer 2 (mg-N/L)
- PON2 = G2 particulate organic nitrogen in layer 2 (mg-N/L)
- PON3 = G3 particulate organic nitrogen in layer 2 (mg-N/L)
- POP1 = G1 particulate organic phosphorus in layer 2 (mg-N/L)
- POP2 = G2 particulate organic phosphorus in layer 2 (mg-N/L)
- POP3 = G3 particulate organic phosphorus in layer 2 (mg-N/L)
**Settling Rates**
According to page 99 of [this very useful resource on the Sediment Diagenesis Module](https://apps.ecology.wa.gov/publications/documents/1703010.pdf), sediments are a constant defined in input. 

### Dec 8, 2022
#### Creating consistent Whidbey labels
The agreed upon labels are:
```
'wqm_baseline':'2014 conditions',
    'wqm_reference':'Reference',
    '3b':'3b: No Whidbey WWTPs',
    '3c':'3f: No Whidbey Rivers',
    '3e':'3c: No Small WWTPs < 100 TN Kg/day ',
    '3f':'3d: No Medium WWTPs 100 to 1000 TN Kg/day',
    '3g':'3e: No Everett North & South WWTPs',
    '3h':'3h: No Everett North (River)',
    '3i':'3i: No Everett South (Deep)',
    '3l':'3l: 0.5x 2014 River Load',
    '3m':'3g: 2x 2014 River Load'
```
NOTE: Management wants to change the run labels and this change will make the run labels different than the way they are organized/referenced on Hyak.  
I am going to keep all references to the runs the same as they are on Hyak until the point of labeling graphics 

For now, I'm just going to focus on the plotting routines.  These are:
- plot_4panel_noncompliant_timeseries.py
- plot_5panel_noncompliant_timeseries.py
- plot_conc_graphics_for_movies.py
- plot_noncompliance_timeseries.py
- IGNORE [old]: plot_noncompliant_graphics4movie_SOGZoom.py
- plot_noncompliant_graphics4movie_whidbeyZoom.py
- plot_percentVolumeHypoxic_movie.py
- plot_threshold_movie.py
- calc_noncompliance.py
- calc_DO_below_threshold.py

Starting with the spreadsheets:
- calc_noncompliance.py
- calc_DO_below_threshold.py


### Dec 5, 2022
#### NPP Workshop 12/06/22
Location of existing and reference output netcdf files:
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/SSM_model_output/NPP_workshop120622_WQM.nc
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/SSM_model_output/NPP_workshop120622_WQM_REF.nc
```


### Nov 10, 2022
#### updates
- Fixed noncompliant calculation to include Min DO reference < DO standard criteria
For benthic case:
```
DO_std = np.tile(gdf.DO_std,(ndays, 1))
DO_diff_lt_0p2[run_type] = (
            (DO_diff<=non_compliant_threshold) &   #361x4144 (nodes x time) or 361x10x4144
            (MinDO[reference] < DO_std)
        )
```
For water column case
```
DO_std = np.tile(gdf.DO_std,(ndays,nlevels,1))
DO_diff_lt_0p2[run_type] = (
            (DO_diff<=non_compliant_threshold) &   #361x4144 (nodes x time) or 361x10x4144
            (MinDO[reference] < DO_std)
        )
```


### Nov 9, 2022

#### updates
- changed hypoxic and concentration plots to show all nodes where model output exists (kept non-compliance graphics to just show un-masked nodes)
- finished correcting language from impaired -> non-compliant
- fixed titles to show date rather than day in year and added date to .png file name for ease of reference
- reprocessed graphics for full domain movies of surface mean daily NO3, surface mean dialy salinity, and min daily DOXG. NO3 processed OK but the others didn't.  Likely running into file quota limits.  Need to address that problem. Temporary solution: delete files.  
- Deleted files in /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics/SOG_NB/DOXG/1*, /2* (i.e. kept the reference and baseline noncompliance zoomed-in graphics)
- Deleted "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics/SOG_NB/NO3".  This was a mistake, but it happened. 



### Oct 10, 2022

Review station file for list of variables.

Location of file: `/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/WQM`


### Sept 28
#### Workshop graphics

NOTE: Whidbey Region zoomed movies were generated for whidbey case, not `SOG_NB`. Do we need for `SOG_NB`?

#####  Movie graphics

Location for DOXG graphics that are zoomed into Whidbey Region:
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics/whidbey/DOXG/3h/movies_whidbeyZoom/conc/wc
```
or, more generally:
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics/${case}/${param}/${run_folders[${SLURM_ARRAY_TASK_ID}]}/movies_whidbeyZoom/conc/${loc}
```
where:
- case: `SOG_NB` or `whidbey`
- param (e.g.): `DOXG`
- `run_folder`: The scenario name
- loc: `wc`,`surface`, or `bottom`

replace `conc/wc` with impairment for impairment graphics. 

#### Workshop movies
Location for movies that are zoomed into the Whidbey Region:
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/movies_whidbeyZoom/whidbey/DOXG/
```

### Sept 14
NEXT: Create salinity movies
Modify code so that graphics are saved to:
`/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/SOG_NB/salinity/movies`
-`/surface/run_tag`
-`/bottom/run_tag`
-`/wc/run_tag`


Figure tasks (Sept 8)
1. [done] Download new shapefile, transfer to Hyak and re-process all runs to incorporate typo corrections.  
2. [done] Nutrient input timeseries graphics for 2014 conditions for all SOG WWTP and Rivers (1x4, 1x7 or 1x8 panels TBD by aesthetics) 
3. [done] Create 6-panel graphic, one for each region, showing impairment timeseries for each scenario.  I thought this would be a slight modification of existing code but I’m now seeing that I need to create a new script to create this graphic.  It will be mostly a copy-paste job with some structural changes that are best done with a fresh start.  I bumped this down in priority given that you have something to work with for now, Joel.  
4. Salinity movies for (a) surface and (b) bottom level.  I think I completed the graphics for the surface movie but haven’t yet looked at them to QAQC.  I ran into a debugging issue that is sorted out now so these ought to go smoothly from here.  
5. NO3 movies for (a) surface and (b) bottom level. I think I completed the graphics for the surface movie but haven’t yet looked at them to QAQC. 

####  Reviewing past work on salinity and NO3 
- Created mean, daily NO3 file for water column, surface and bottom in `process_netcdf_NO3.sh`
```
python process_netcdf.py ${file_path} "NO3" "SOG_NB" "mean" 1 1
```
- Created mean, daily salinity files for water column, surface and bottom in `process_netcdf_salinity.sh
```
python process_netcdf.py ${file_path} "salinity" "SOG_NB" "mean" 1 1
```
- Created `.png` files for movies
Surface, daily-mean salinity graphics
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/SOG_NB/salinity/movies/surface
```




### Aug 22
#####  Installing FFMPEG on Hyak using Aptainer

From Matt:
```
Yes, you can install anything you want to either your private gscratch space or the 'contrib' area and then create a module for it if you wish: https://hyak.uw.edu/docs/tools/modules#how-do-i-create-personal-lmod-modules-on-klone

Alternatively you can create an Apptainer (formerly Singularity) container with program (sometimes this is easier because you can use existing Docker images to build the container, or use apt-get/yum in the container host OS to install the software), and run applications via container: https://hyak.uw.edu/docs/tools/containers

We encourage the container route as it is where things are going in HPC, and is more conducive to reproducible research than local installed software.
```
On Hyak (Klone):
I have my environment setup such that $HOME is 
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael
```
1. I first moved to this directory and then initiated an interactive node:
```
(base) [rdmseas@klone1 ~]$ allocate2
salloc: Pending job allocation 5899458
salloc: job 5899458 queued and waiting for resources
salloc: job 5899458 has been allocated resources
salloc: Granted job allocation 5899458
salloc: Waiting for resource configuration
salloc: Nodes n3288 are ready for job
```
2. I loaded aptainer
```
module load apptainer
```
3. Create an Apptainer definition file.  I call the following file ffmpeg.def and placed it in an `app_defs` folder in my $HOME directory:
```
mkdir app_defs
cd app_defs
vi ffmpeg.def
```
and wrote the following to the `ffmpeg.def` file:
```
Bootstrap: docker
From: ubuntu:16.04
%post
    apt -y update
    apt -y install ffmpeg
```
4. Following the UW-IT support instructions: Build a Apptainer container from its definition file. The generated SIF file is your portable container.

The .def definition file should either be A) executable or B) a relative path (e.g. ./tools.def while in the same directory as the file) or an absolute path (e.g. /full/path/to/tools.def).

When using the --fakeroot option, build the container image in /tmp. This avoids [a potential permission issue] with our shared storage filesystem, GPFS.
```
(base) [rdmseas@n3288 app_defs]$ apptainer build --fakeroot /tmp/ffmpeg.sif ./ffmpeg.def
WARNING: Not compiled with seccomp, fakeroot may not work correctly, if you get permission denied error during creation of pseudo devices, you should install seccomp library and recompile Apptainer
INFO:    Starting build...
FATAL:   While performing build: conveyor failed to get: loading registries configuration: reading registries.conf.d: lstat /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.config/containers/registries.conf.d: permission denied
(base) [rdmseas@n3288 app_defs]$ 

```
##### Installing ffmpeg using LMOD module

```
cd /sw/contrib/
(base) [rdmseas@n3288 contrib]$ ls ssmc-*
ssmc-dev-src:

ssmc-src:
miniconda/  nco/  netcdf/
(base) [rdmseas@n3288 contrib]$ ls modulefiles/ssmc
miniconda/  netcdf/
```

### July 11


##### Processing by interactive node
Parallel processing using batch script wasn't working, so I'm doing one at a time
**Baseline**
```
(base) [rdmseas@klone1 scripts]$ allocate2
salloc: Pending job allocation 5240464
salloc: job 5240464 queued and waiting for resources
salloc: job 5240464 has been allocated resources
salloc: Granted job allocation 5240464
salloc: Waiting for resource configuration
salloc: Nodes n3015 are ready for job
(base) [rdmseas@n3015 scripts]$ module load foster/python/miniconda/3.8
(base) [rdmseas@n3015 scripts]$ source /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/etc/profile.d/conda.sh
(base) [rdmseas@n3015 scripts]$ conda activate klone_jupyter
(klone_jupyter) [rdmseas@n3015 scripts]$ python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/wqm_baseline/ssm_output.nc"
wqm_baseline
```
**1b_all_sog_wwtp_off**
```
(klone_jupyter) [rdmseas@n3015 scripts]$ python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1b_all_sog_wwtp_off/ssm_output.nc"
1b_all_sog_wwtp_off
creating: /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/DOXG/1b_all_sog_wwtp_off/bottom
***********************************************************
processing:  /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1b_all_sog_wwtp_off/ssm_output.nc
8784 10 16012
Saving to file:1b_all_sog_wwtp_off/dailyDO_24hrmin.nc
Saving to file:1b_all_sog_wwtp_off/bottom/dailyDO_24hrmin_bottom.nc
```
**1c_all_sog_riv_off**
```
(klone_jupyter) [rdmseas@n3319 scripts]$ python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1c_all_sog_riv_off/ssm_output.nc"
1c_all_sog_riv_off
creating: /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/DOXG/1c_all_sog_riv_off/bottom
***********************************************************
processing:  /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1c_all_sog_riv_off/ssm_output.nc
8784 10 16012
Traceback (most recent call last):
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 69, in <module>
    process_netcdf(args[0])
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 48, in process_netcdf
    dailyDO = reshape_fvcom3D(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/ssm_utils.py", line 180, in reshape_fvcom3D
    fvcom_timeIJK[:,:,:].data, (366,24,zi,ni)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/dataarray.py", line 627, in data
    return self.variable.data
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 339, in data
    return self.values
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 512, in values
    return _as_array_or_item(self._data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 252, in _as_array_or_item
    data = np.asarray(data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 552, in __array__
    self._ensure_cached()
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 549, in _ensure_cached
    self.array = NumpyIndexingAdapter(np.asarray(self.array))
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 522, in __array__
    return np.asarray(self.array, dtype=dtype)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 423, in __array__
    return np.asarray(array[self.key], dtype=None)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 93, in __getitem__
    return indexing.explicit_indexing_adapter(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 712, in explicit_indexing_adapter
    result = raw_indexing_method(raw_key.tuple)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 106, in _getitem
    array = getitem(original_array, key)
  File "src/netCDF4/_netCDF4.pyx", line 4406, in netCDF4._netCDF4.Variable.__getitem__
  File "src/netCDF4/_netCDF4.pyx", line 5350, in netCDF4._netCDF4.Variable._get
  File "src/netCDF4/_netCDF4.pyx", line 1927, in netCDF4._netCDF4._ensure_nc_success
RuntimeError: NetCDF: HDF error
```

```
(klone_jupyter) [rdmseas@n3015 scripts]$ python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1d_small_sog_wwtp_off/ssm_output.nc"
1d_small_sog_wwtp_off
***********************************************************
processing:  /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1d_small_sog_wwtp_off/ssm_output.nc
8784 10 16012
Traceback (most recent call last):
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 69, in <module>
    process_netcdf(args[0])
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 48, in process_netcdf
    dailyDO = reshape_fvcom3D(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/ssm_utils.py", line 180, in reshape_fvcom3D
    fvcom_timeIJK[:,:,:].data, (366,24,zi,ni)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/dataarray.py", line 627, in data
    return self.variable.data
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 339, in data
    return self.values
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 512, in values
    return _as_array_or_item(self._data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 252, in _as_array_or_item
    data = np.asarray(data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 552, in __array__
    self._ensure_cached()
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 549, in _ensure_cached
    self.array = NumpyIndexingAdapter(np.asarray(self.array))
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 522, in __array__
    return np.asarray(self.array, dtype=dtype)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 423, in __array__
    return np.asarray(array[self.key], dtype=None)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 93, in __getitem__
    return indexing.explicit_indexing_adapter(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 712, in explicit_indexing_adapter
    result = raw_indexing_method(raw_key.tuple)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 106, in _getitem
    array = getitem(original_array, key)
  File "src/netCDF4/_netCDF4.pyx", line 4406, in netCDF4._netCDF4.Variable.__getitem__
  File "src/netCDF4/_netCDF4.pyx", line 5350, in netCDF4._netCDF4.Variable._get
  File "src/netCDF4/_netCDF4.pyx", line 1927, in netCDF4._netCDF4._ensure_nc_success
RuntimeError: NetCDF: HDF error
```
Same with 1e
```
(klone_jupyter) [rdmseas@n3015 scripts]$ python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1e_med_sog_wwtp_off/ssm_output.nc"
1e_med_sog_wwtp_off
creating: /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/DOXG/1e_med_sog_wwtp_off/bottom
***********************************************************
processing:  /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1e_med_sog_wwtp_off/ssm_output.nc
8784 10 16012
Traceback (most recent call last):
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 69, in <module>
    process_netcdf(args[0])
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 48, in process_netcdf
    dailyDO = reshape_fvcom3D(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/ssm_utils.py", line 180, in reshape_fvcom3D
    fvcom_timeIJK[:,:,:].data, (366,24,zi,ni)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/dataarray.py", line 627, in data
    return self.variable.data
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 339, in data
    return self.values
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 512, in values
    return _as_array_or_item(self._data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 252, in _as_array_or_item
    data = np.asarray(data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 552, in __array__
    self._ensure_cached()
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 549, in _ensure_cached
    self.array = NumpyIndexingAdapter(np.asarray(self.array))
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 522, in __array__
    return np.asarray(self.array, dtype=dtype)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 423, in __array__
    return np.asarray(array[self.key], dtype=None)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 93, in __getitem__
    return indexing.explicit_indexing_adapter(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 712, in explicit_indexing_adapter
    result = raw_indexing_method(raw_key.tuple)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 106, in _getitem
    array = getitem(original_array, key)
  File "src/netCDF4/_netCDF4.pyx", line 4406, in netCDF4._netCDF4.Variable.__getitem__
  File "src/netCDF4/_netCDF4.pyx", line 5350, in netCDF4._netCDF4.Variable._get
  File "src/netCDF4/_netCDF4.pyx", line 1927, in netCDF4._netCDF4._ensure_nc_success
RuntimeError: NetCDF: HDF error
```
River forcing worked
**2a_sog_river_0.5times**
```
(klone_jupyter) [rdmseas@n3015 scripts]$ python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/2a_sog_river_0.5times/ssm_output.nc"
2a_sog_river_0.5times
creating: /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/DOXG/2a_sog_river_0.5times/bottom
***********************************************************
processing:  /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/2a_sog_river_0.5times/ssm_output.nc
8784 10 16012
Saving to file:2a_sog_river_0.5times/dailyDO_24hrmin.nc
Saving to file:2a_sog_river_0.5times/bottom/dailyDO_24hrmin_bottom.nc
```
Not **2.0times**
```
(klone_jupyter) [rdmseas@n3015 scripts]$ python process_netcdf.py "/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/2b_sog_river_2times/ssm_output.nc"
2b_sog_river_2times
creating: /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/DOXG/2b_sog_river_2times/bottom
***********************************************************
processing:  /mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/2b_sog_river_2times/ssm_output.nc
8784 10 16012
Traceback (most recent call last):
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 69, in <module>
    process_netcdf(args[0])
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.py", line 48, in process_netcdf
    dailyDO = reshape_fvcom3D(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/ssm_utils.py", line 180, in reshape_fvcom3D
    fvcom_timeIJK[:,:,:].data, (366,24,zi,ni)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/dataarray.py", line 627, in data
    return self.variable.data
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 339, in data
    return self.values
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 512, in values
    return _as_array_or_item(self._data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/variable.py", line 252, in _as_array_or_item
    data = np.asarray(data)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 552, in __array__
    self._ensure_cached()
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 549, in _ensure_cached
    self.array = NumpyIndexingAdapter(np.asarray(self.array))
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 522, in __array__
    return np.asarray(self.array, dtype=dtype)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 423, in __array__
    return np.asarray(array[self.key], dtype=None)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 93, in __getitem__
    return indexing.explicit_indexing_adapter(
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/core/indexing.py", line 712, in explicit_indexing_adapter
    result = raw_indexing_method(raw_key.tuple)
  File "/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda/envs/klone_jupyter/lib/python3.10/site-packages/xarray/backends/netCDF4_.py", line 106, in _getitem
    array = getitem(original_array, key)
  File "src/netCDF4/_netCDF4.pyx", line 4406, in netCDF4._netCDF4.Variable.__getitem__
  File "src/netCDF4/_netCDF4.pyx", line 5350, in netCDF4._netCDF4.Variable._get
  File "src/netCDF4/_netCDF4.pyx", line 1927, in netCDF4._netCDF4._ensure_nc_success
RuntimeError: NetCDF: HDF error
```

#####  Files that need to be quality controlled:

```
/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1c_all_sog_riv_off/ssm_output.nc
/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1d_small_sog_wwtp_off/ssm_output.nc
/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/1e_med_sog_wwtp_off/ssm_output.nc
/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/kingcounty/2b_sog_river_2times/ssm_output.nc
```
### July 10
##### Submit parallel process\_netcdf job
```
(base) [rdmseas@klone1 scripts]$ sbatch process_netcdf.sh
Submitted batch job 5238183
(base) [rdmseas@klone1 scripts]$ scontrol show job -d  5238183
JobId=5238183 JobName=SSM_netcdf
   UserId=rdmseas(1287748) GroupId=all(226269) MCS_label=N/A
   Priority=2067 Nice=0 Account=ssmc QOS=ssmc
   JobState=COMPLETED Reason=None Dependency=(null)
   Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   DerivedExitCode=0:0
   RunTime=00:00:11 TimeLimit=05:00:00 TimeMin=N/A
   SubmitTime=2022-07-10T21:55:45 EligibleTime=2022-07-10T21:55:45
   AccrueTime=2022-07-10T21:55:45
   StartTime=2022-07-10T21:55:45 EndTime=2022-07-10T21:55:56 Deadline=N/A
   PreemptEligibleTime=2022-07-10T21:55:45 PreemptTime=None
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2022-07-10T21:55:45 Scheduler=Main
   Partition=compute AllocNode:Sid=klone-login01:2570181
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=n[3227-3233]
   BatchHost=n3227
   NumNodes=7 NumCPUs=7 NumTasks=7 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
   TRES=cpu=7,mem=1225G,node=7,billing=252
   Socks/Node=* NtasksPerN:B:S:C=1:0:*:* CoreSpec=*
   JOB_GRES=(null)
     Nodes=n[3227-3233] CPU_IDs=0 Mem=179200 GRES=
   MinCPUsNode=1 MinMemoryNode=175G MinTmpDiskNode=0
   Features=(null) DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.sh
   WorkDir=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts
   StdErr=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/slurm-5238183.out
   StdIn=/dev/null
   StdOut=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/slurm-5238183.out
   Power=

```

```
(base) [rdmseas@klone1 scripts]$ sbatch process_netcdf.sh
Submitted batch job 5237797

(base) [rdmseas@klone1 scripts]$ scontrol show job -d 5237797
JobId=5237797 JobName=SSM_netcdf
   UserId=rdmseas(1287748) GroupId=all(226269) MCS_label=N/A
   Priority=2067 Nice=0 Account=ssmc QOS=ssmc
   JobState=RUNNING Reason=None Dependency=(null)
   Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   DerivedExitCode=0:0
   RunTime=00:00:46 TimeLimit=02:00:00 TimeMin=N/A
   SubmitTime=2022-07-10T16:53:49 EligibleTime=2022-07-10T16:53:49
   AccrueTime=2022-07-10T16:53:49
   StartTime=2022-07-10T16:53:51 EndTime=2022-07-10T18:53:51 Deadline=N/A
   PreemptEligibleTime=2022-07-10T16:53:51 PreemptTime=None
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2022-07-10T16:53:51 Scheduler=Main
   Partition=compute AllocNode:Sid=klone-login01:2570181
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=n[3250-3251,3256-3258,3260,3274]
   BatchHost=n3250
   NumNodes=7 NumCPUs=7 NumTasks=7 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
   TRES=cpu=7,mem=1225G,node=7,billing=252
   Socks/Node=* NtasksPerN:B:S:C=1:0:*:* CoreSpec=*
   JOB_GRES=(null)
     Nodes=n[3250-3251,3256-3258,3260,3274] CPU_IDs=0 Mem=179200 GRES=
   MinCPUsNode=1 MinMemoryNode=175G MinTmpDiskNode=0
   Features=(null) DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.sh
   WorkDir=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts
   StdErr=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/slurm-5237797.out
   StdIn=/dev/null
   StdOut=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/slurm-5237797.out
   Power=
   

```

```
(base) [rdmseas@klone1 scripts]$ scontrol show job -d 5237793
JobId=5237793 JobName=SSM_netcdf
   UserId=rdmseas(1287748) GroupId=all(226269) MCS_label=N/A
   Priority=2067 Nice=0 Account=ssmc QOS=ssmc
   JobState=COMPLETED Reason=None Dependency=(null)
   Requeue=1 Restarts=0 BatchFlag=1 Reboot=0 ExitCode=0:0
   DerivedExitCode=0:0
   RunTime=00:00:58 TimeLimit=02:00:00 TimeMin=N/A
   SubmitTime=2022-07-10T16:46:33 EligibleTime=2022-07-10T16:46:33
   AccrueTime=2022-07-10T16:46:33
   StartTime=2022-07-10T16:46:34 EndTime=2022-07-10T16:47:32 Deadline=N/A
   PreemptEligibleTime=2022-07-10T16:46:34 PreemptTime=None
   SuspendTime=None SecsPreSuspend=0 LastSchedEval=2022-07-10T16:46:34 Scheduler=Main
   Partition=compute AllocNode:Sid=klone-login01:2570181
   ReqNodeList=(null) ExcNodeList=(null)
   NodeList=n[3248,3250-3251,3256-3258,3277]
   BatchHost=n3248
   NumNodes=7 NumCPUs=7 NumTasks=7 CPUs/Task=1 ReqB:S:C:T=0:0:*:*
   TRES=cpu=7,mem=1225G,node=7,billing=252
   Socks/Node=* NtasksPerN:B:S:C=1:0:*:* CoreSpec=*
   JOB_GRES=(null)
     Nodes=n[3248,3250-3251,3256-3258,3277] CPU_IDs=0 Mem=179200 GRES=
   MinCPUsNode=1 MinMemoryNode=175G MinTmpDiskNode=0
   Features=(null) DelayBoot=00:00:00
   OverSubscribe=OK Contiguous=0 Licenses=(null) Network=(null)
   Command=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/process_netcdf.sh
   WorkDir=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts
   StdErr=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/slurm-5237793.out
   StdIn=/dev/null
   StdOut=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/KingCounty-Rachael/scripts/slurm-5237793.out
   Power=
```
### July 1
##### Meeting with KC modeling group (Stefano, Su Kyong)
- time series graphics for selected nodes
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/graphics
```
### June 28
#####  Meeting with Joel (KC Modeling Project) 
Discussed progress, including:
- Running Ben's C++ code (22 hours -> v4-like NetCDF)
- Running Ben's python code 
- MEG meeting (fluxes)
	1. Fluxes: Flux of carbon(or nitrogen) to the sediment at any given node
	2. How much nitrogen crosses the photic zone? 
- Output files (BIG: history files, small: station files)
- KC tasks (from Marielle):
	1. First step: Summary of what we know now in terms of model error and calibration results. Stefano highlighted that the technical report will be due soon.  
	2. Longer term: Fill in some of the gaps based on the uncertainty analysis the Model Evaluation Group requests

For next time: 
- Outline of KC tech report (Stefano)
- Check netcdf for x-,y- coordinates (I did.  They aren't there)
- Summary of netcdf model output from Ben and comparison with previous (Rachael)
- QAQC of model output using station output files (Su Kyong)
- Evaluate what has been done (with other models?) in the realm of evaluating passive tracers in WWTP discharge.  Determine whether adding tracers to SSM run(s)is a simple/straightforward/low-hanging-fruit ask. 
- Work toward a table of # of days impared DO by basin and volume days impared DO by basin

### June 27
Finalize script for identifying the closest SSMC cell id to a particular lat/lon. 

##### Projecting a lat/lon pair

[pyproj Transformer](https://pyproj4.github.io/pyproj/stable/api/transformer.html)

[WGS](https://en.wikipedia.org/wiki/World_Geodetic_System)
[EPSG:32610](https://www.google.com/search?client=safari&rls=en&q=EPSG%3A32610&ie=UTF-8&oe=UTF-8) is a projected coordinate system for our region
### June 23
Wilmot (2021), scales from [0,1] is better at handling extreme values than previous versions [0,1]

Evaluation purpose:
1) compare with other models.  Use standard metrics.
2) Evaluate model. plot up model vs. observation. 
  - Fit line
  - Compare fit to 1:1 line
  - RMS difference between value and fit
  - RMS difference bettween value and 1:1
Are all oxygen levels low? (systematic error) or is it scatter (not systematic) 
3) Evaluate how to improve model. Isolate processes


Susan: consider nitrate-salinity comparison to get away from issues related to tthe accuracy of plume location.  Do they have a similar look between model and obs?

Kling-Gupta equations
Quantile/quantile plots

[Python HydroErr toolbox](https://pypi.org/project/HydroErr/) and [the paper](https://www.sciencedirect.com/science/article/abs/pii/S136481521930427X)

How well should a model compare with observations if data is at a particular time and location whereas a model is an average over time
### June 13, 2022
##### Fixing messed up Git repo

Tried to checkout earlier version but was thwarted by `.ipynb_checkpoints` changes

Created .gitignore with the following:
```
.ipynb_checkpoints
*/.ipynb_checkpoints/*
```

Tried to checkout earlier commit but was refused because of changes to 
`RegionalNodeCount.ipynb`

```
(base) [rdmseas@klone1 KingCounty-Rachael]$ git checkout 49367397ca0af1b872526ebd7308947a41896aaa
error: The following untracked working tree files would be overwritten by checkout:
	notebooks/RegionalNodeCount.ipynb
Please move or remove them before you switch branches.
Aborting
(base) [rdmseas@klone1 KingCounty-Rachael]$ git status
On branch main
Your branch is up to date with 'origin/main'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.ipynb_checkpoints/
	SuKyongs_python/.ipynb_checkpoints/
...
```
Tried to remove file but was told that it doesn't exist
```
(base) [rdmseas@klone1 KingCounty-Rachael]$ git rm notebooks/RegionalNodeCount.ipynb
fatal: pathspec 'notebooks/RegionalNodeCount.ipynb' did not match any files
(base) [rdmseas@klone1 KingCounty-Rachael]$ ls notebooks/
dev_daily_min_graphic.ipynb    dev_volume_calc.ipynb
dev_DO_histogram.ipynb         qaqc_regional_node_count.ipynb
dev_minSalinity.ipynb          RegionalNodeCount.ipynb
dev_TS_ExistRef_graphic.ipynb
```
So strange!
I ended up removing the file outside of `git`
```
(base) [rdmseas@klone1 KingCounty-Rachael]$ rm notebooks/RegionalNodeCount.ipynb 
rm: remove regular file 'notebooks/RegionalNodeCount.ipynb'? y
(base) [rdmseas@klone1 KingCounty-Rachael]$ git checkout 49367397ca0af1b872526ebd7308947a41896aaa
Note: switching to '49367397ca0af1b872526ebd7308947a41896aaa'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -c with the switch command. Example:

  git switch -c <new-branch-name>

Or undo this operation with:

  git switch -

Turn off this advice by setting config variable advice.detachedHead to false

HEAD is now at 4936739 debug in progress for netcdf4 access
```
Created a new branch
```
$ git switch -c "FixGit"
$ git branch
* FixGit
  main
```

There are only four notebooks in this branch
```
(base) [rdmseas@klone1 notebooks]$ ls
dev_daily_min_graphic.ipynb  dev_minSalinity.ipynb
dev_DO_histogram.ipynb       RegionalNodeCount.ipynb
```
Starting a remote JupyterLab session to compare these notebooks to those in most recent commit. 

The files that became corrupted include:
-dev_minSalinity


### May 19, 2022
##### Unistalling miniconda from $HOME
I've already removed the miniconda directory but the setup was still pointed to $HOME.  Fixing that here. 
1. Removed all miniconda related entries in my `~/.bashrc` file
2. Removed all miniconda related `~/.*` files
```
[rdmseas@klone1 outputs]$ rm -rf ~/.conda
[rdmseas@klone1 outputs]$ rm -rf ~/.condarc
```
3. Change directory to lab group space
```
/mmfs1/gscratch/ssmc/PSI/Rachael
```
4. Deleted the miniconda3 folder that I had moved here from `$HOME` so that I could start clean
```

```

### May 13, 2022
Created Git repositories

##### Debug issue with transect_png.py

Submitted new run
```
[rdmseas@klone1 sukyong_scripts]$ sbatch transect_png.sh
Submitted batch job 4532752
```
### May 12,2022
##### Creating/debugging function for min values
Starting interactive node (~30s)
```
[rdmseas@klone1 sukyong_script]$ salloc -A ssmc -p compute -N 1 -c 1 --mem=175G --time=1:00:00
salloc: Pending job allocation 4528463
salloc: job 4528463 queued and waiting for resources
salloc: job 4528463 has been allocated resources
salloc: Granted job allocation 4528463
salloc: Waiting for resource configuration
salloc: Nodes n3290 are ready for job
```
##### Submitting script for calculating min to compare with results from original
```
[rdmseas@klone1 sukyong_scripts]$ sbatch daily_min_data_extract_function.sh
Submitted batch job 4528684
```
SUCCESS!

##### Setup jupyterlab environment on Hyak
**installing miniconda**
```
[rdmseas@klone1 ~]$ pwd
/mmfs1/home/rdmseas
[rdmseas@klone1 ~]$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
--2022-05-12 14:51:44--  https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
Resolving repo.anaconda.com (repo.anaconda.com)... 104.16.131.3, 104.16.130.3, 2606:4700::6810:8303, ...
Connecting to repo.anaconda.com (repo.anaconda.com)|104.16.131.3|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 75660608 (72M) [application/x-sh]
Saving to: ‘Miniconda3-latest-Linux-x86_64.sh’

Miniconda3-latest-Linux-x86_ 100%[=============================================>]  72.16M  89.9MB/s    in 0.8s    

2022-05-12 14:51:45 (89.9 MB/s) - ‘Miniconda3-latest-Linux-x86_64.sh’ saved [75660608/75660608]

[rdmseas@klone2 rachael-ssmc]$ cd /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/envs
[rdmseas@klone2 envs]$ ls
klone-jupyter.yml
[rdmseas@klone2 envs]$ module load foster/python/miniconda/3.8
[rdmseas@klone2 envs]$ conda env create -f ./klone-jupyter.yml
Collecting package metadata (repodata.json): done
Solving environment: done


==> WARNING: A newer version of conda exists. <==
  current version: 4.10.3
  latest version: 4.12.0

Please update conda by running

    $ conda update -n base -c defaults conda


^C^Cç
Downloading and Extracting Packages
...

[Errno 122] Disk quota exceeded
[Errno 122] Disk quota exceeded: '/mmfs1/home/rdmseas/.conda/pkgs/openjpeg-2.4.0-hb52868f_1/info/repodata_record.json'
[Errno 122] Disk quota exceeded: '/mmfs1/home/rdmseas/.conda/pkgs/yaml-0.2.5-h7f98852_2/info/repodata_record.json'
[Errno 122] Disk quota exceeded
[Errno 122] Disk quota exceeded
```


### May 11, 2022
##### Meeting with Stefano
- Completed all onboarding training except Ethics (scheduled for next Wed).  Last remaining is to sign up for benefits/retirement
- Worked with IT to fix Hyak `account` and `partition` information.  New error today:
```
batch: error: QOSMaxMemoryPerNode
sbatch: error: Batch job submission failed: Job violates accounting/QOS policy (job submit limit, user's size and/or time limits)
``` 
Sent an email to Tarang and UW IT:
```
It seems that my account is lacking a sufficient “job submit limit”, “user’s size”, and/or “time limit” to run the script(s) that I will be required to run as a part of my job.  Tarang, can you please work with IT help to resolve this mis-match between job requirement and resources?  Alternatively, I’m all ears to learning a way to run these scripts within my given resources
```
Waiting to hear back
- Creating an overview of scripts to use for the purpose of learning and code development
- Scheduled meeting with Sukyong for this Friday
- Review priorities.  I proposed:
	1. to learn the workflow described in planar_transect_scripts.ppt  
	2. familiarize myself with scripts and run them
	3. re-generate the existing graphics using the newer set of model results and the existing scripts.
	4. update or create new scripts to advance visual display and/or information 

To Do:
- Ask Kevin for the paths for files used to create the 

##### Run scripts for DO, "as is"
**Daily Average**
```
[rdmseas@klone1 sukyong_scripts]$ sbatch daily_average_data_extract.sh
Submitted batch job 4526646
```
The output was:
```
starting the run
Wed May 11 18:39:01 PDT 2022
Wed May 11 18:46:08 PDT 2022
run ended
```
The save directory is defined in as:
```
save_directory='/mmfs1/home/rdmseas/projects/ssmc/rachael-ssmc/output/gis_output_do'
```
The file is saved to: 
```
/mmfs1/home/rdmseas/projects/ssmc/rachael-ssmc/output/gis_output_do2014_SSM4_WQ_rvr_ref_reg_DO_depth_average.csv
```
Update code to use `Path` so that user specification of directory name as directory path (i.e. the "\" requirement) isn't neccessary
**Daily Min**
```
[rdmseas@klone1 sukyong_scripts]$ sbatch daily_min_data_extract.sh
Submitted batch job 4526663
```
The output was:
```
starting the run
Wed May 11 18:48:36 PDT 2022
Wed May 11 18:53:12 PDT 2022
run ended
```
The save directory is defined in `daily_min_data_extract.py` as:
```
save_directory='/mmfs1/home/rdmseas/projects/ssmc/rachael-ssmc/output/daily_min'
```
but the `.pkl` files were save to the directory where the script is run rather than the specified `save_directory`.

**Transects**
```
[rdmseas@klone1 sukyong_scripts]$ sbatch transect_png.sh
Submitted batch job 4526697
```
The ouput was:
```
starting the run
Wed May 11 18:52:37 PDT 2022
Traceback (most recent call last):
  File "transect_png.py", line 36, in <module>
    transect_node_index=pd.read_csv(transect_directory).node_id-1
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/util/_decorators.py", line 311, in wrapper
    return func(*args, **kwargs)
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/io/parsers/readers.py", line 586, in read_csv
    return _read(filepath_or_buffer, kwds)
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/io/parsers/readers.py", line 482, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/io/parsers/readers.py", line 811, in __init__
    self._engine = self._make_engine(self.engine)
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/io/parsers/readers.py", line 1040, in _make_engine
    return mapping[engine](self.f, **self.options)  # type: ignore[call-arg]
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/io/parsers/c_parser_wrapper.py", line 51, in __init__
    self._open_handles(src, kwds)
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/io/parsers/base_parser.py", line 222, in _open_handles
    self.handles = get_handle(
  File "/sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/pandas/io/common.py", line 701, in get_handle
    handle = open(
FileNotFoundError: [Errno 2] No such file or directory: 'transect_node_id.csv'
Wed May 11 18:53:00 PDT 2022
```
### May 6, 2022
- Activated Hyak [following these Logging In instructions](https://wiki.cac.washington.edu/display/hyakusers/Logging+In)
- Logged into Hyak
```
ssh -X RDMseas@klone.hyak.uw.edu
```
- Setting up environment in `~/.bashrc`
- Reviewing modules
```
[rdmseas@klone1 ~]$ module avail | grep python
   cesg/python/3.8.10                       stf/bwa/0.7.17
   foster/python/miniconda/3.8              stf/petsc/mpich/3
```
##### Setting up my Jupyter environment 
Look like Hyak uses conda as a package manager.  See [Hyak python programming](https://wiki.cac.washington.edu/display/hyakusers/Hyak+python+programming)
##### Hyak group name and user ID
Below xyz is your group name and abc is your userid. 
**My group name is**:
**My userid is**: `rdmseas`
From Sukyong's email, I'm seeing `/mmfs1/gscratch/ssmc/USRS/PSI/Sukyong/script`
Created `/gscratch/ssmc/USRS/PSI/Rachael`
```
[Miniconda instructions](https://hyak.uw.edu/docs/tools/python/)
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
```
Where `$HOME` is set to `/mmfs1/home/rdmseas`
Create an environment in lab directory because "We discourage using your home directory as you will likely hit your inode (i.e., file) limits." 

(note: I did this part on May 12th)
I choose `/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/`

Next, initialize shell

```
$module load foster/python/miniconda/3.8 
$conda init bash
no change     /sw/contrib/foster-src/python/miniconda/3.8/condabin/conda
no change     /sw/contrib/foster-src/python/miniconda/3.8/bin/conda
no change     /sw/contrib/foster-src/python/miniconda/3.8/bin/conda-env
no change     /sw/contrib/foster-src/python/miniconda/3.8/bin/activate
no change     /sw/contrib/foster-src/python/miniconda/3.8/bin/deactivate
no change     /sw/contrib/foster-src/python/miniconda/3.8/etc/profile.d/conda.sh
no change     /sw/contrib/foster-src/python/miniconda/3.8/etc/fish/conf.d/conda.fish
no change     /sw/contrib/foster-src/python/miniconda/3.8/shell/condabin/Conda.psm1
no change     /sw/contrib/foster-src/python/miniconda/3.8/shell/condabin/conda-hook.ps1
no change     /sw/contrib/foster-src/python/miniconda/3.8/lib/python3.8/site-packages/xontrib/conda.xsh
no change     /sw/contrib/foster-src/python/miniconda/3.8/etc/profile.d/conda.csh
modified      /mmfs1/home/rdmseas/.bashrc

==> For changes to take effect, close and re-open your current shell. <==
```
logged out and back in.  Now `(base)` shows up at the base of terminal, indicated that miniconda3 is active.  

Next: keep miniconda3 deactivated until called
```
conda config --set auto_activate_base false
```
use `conda activate` before each use and unload it with `conda deactivate`

**create a miniconda environment using a .yml file**

```
$ cd /gscratch/ssmc/USRS/PSI/Rachael/envs/
$ module load foster/python/miniconda/3.8
$ conda env create -f ./klone-jupyter.yml

Collecting package metadata (repodata.json): done
Solving environment: done


==> WARNING: A newer version of conda exists. <==
  current version: 4.10.3
  latest version: 4.12.0

Please update conda by running

    $ conda update -n base -c defaults conda


Downloading and Extracting Packages
sip-6.5.1            | 373 KB    | ######################################################################## | 100% 
libxml2-2.9.14       | 770 KB    | ######################################################################## | 100% 
libbrotlidec-1.0.9   | 33 KB     | ######################################################################## | 100% 
font-ttf-source-code | 684 KB    | ######################################################################## | 100% 
gettext-0.19.8.1     | 3.6 MB    | ######################################################################## | 100% 
libxcb-1.13          | 391 KB    | ######################################################################## | 100% 
xorg-libxdmcp-1.1.3  | 19 KB     | ######################################################################## | 100% 
scipy-1.8.0          | 25.7 MB   | ######################3                                                  |  31% 
libsodium-1.0.18     | 366 KB    | ######################################################################## | 100% 
python-3.10.4        | 28.7 MB   | ####################                                                     |  28% 
mysql-libs-8.0.29    | 1.9 MB    | ######################################################################## | 100% 
jupyterlab_server-2. | 49 KB     | ######################################################################## | 100% 
icu-70.1             | 13.5 MB   | ##########################################5                              |  59% 
shapely-1.8.2        | 363 KB    | ######################################################################## | 100% 
jack-1.9.18          | 640 KB    | ######################################################################## | 100% 
geos-3.10.2          | 1.6 MB    | ######################################################################## | 100% 
attrs-21.4.0         | 49 KB     | ######################################################################## | 100% 
lerc-3.0             | 216 KB    | ######################################################################## | 100% 
libedit-3.1.20191231 | 121 KB    | ######################################################################## | 100% 
readline-8.1         | 295 KB    | ######################################################################## | 100% 
zlib-1.2.11          | 88 KB     | ######################################################################## | 100% 
entrypoints-0.4      | 9 KB      | ######################################################################## | 100% 
python-dateutil-2.8. | 240 KB    | ######################################################################## | 100% 
libflac-1.3.4        | 474 KB    | ######################################################################## | 100% 
psutil-5.9.0         | 350 KB    | ######################################################################## | 100% 
attr-2.5.1           | 69 KB     | ######################################################################## | 100% 
libzlib-1.2.11       | 60 KB     | ######################################################################## | 100% 
pyqt5-sip-12.9.0     | 85 KB     | ######################################################################## | 100% 
cffi-1.15.0          | 433 KB    | ######################################################################## | 100% 
brotli-bin-1.0.9     | 19 KB     | ######################################################################## | 100% 
libxkbcommon-1.0.3   | 581 KB    | ######################################################################## | 100% 
libglib-2.70.2       | 3.1 MB    | ######################################################################## | 100% 
cartopy-0.20.2       | 1.7 MB    | ######################################################################## | 100% 
krb5-1.19.3          | 1.4 MB    | ######################################################################## | 100% 
dbus-1.13.6          | 604 KB    | ######################################################################## | 100% 
pulseaudio-14.0      | 1.6 MB    | ######################################################################## | 100% 
ptyprocess-0.7.0     | 16 KB     | ######################################################################## | 100% 
pyaml-21.10.1        | 20 KB     | ######################################################################## | 100% 
notebook-6.4.11      | 6.3 MB    | ######################################################################## | 100% 
libnghttp2-1.47.0    | 808 KB    | ######################################################################## | 100% 
tzdata-2022a         | 121 KB    | ######################################################################## | 100% 
tinycss2-1.1.1       | 23 KB     | ######################################################################## | 100% 
openssl-1.1.1o       | 2.1 MB    | ######################################################################## | 100% 
certifi-2021.10.8    | 145 KB    | ######################################################################## | 100% 
prometheus_client-0. | 49 KB     | ######################################################################## | 100% 
anyio-3.5.0          | 154 KB    | ######################################################################## | 100% 
terminado-0.13.3     | 27 KB     | ######################################################################## | 100% 
jupyter_server-1.17. | 238 KB    | ######################################################################## | 100% 
alsa-lib-1.2.3.2     | 554 KB    | ######################################################################## | 100% 
pygments-2.12.0      | 817 KB    | ######################################################################## | 100% 
importlib_resources- | 22 KB     | ######################################################################## | 100% 
libblas-3.9.0        | 12 KB     | ######################################################################## | 100% 
gstreamer-1.20.2     | 2.0 MB    | ######################################################################## | 100% 
markupsafe-2.1.1     | 22 KB     | ######################################################################## | 100% 
pandoc-2.18          | 12.5 MB   | ##############################################                           |  64% 
pyopenssl-22.0.0     | 49 KB     | ######################################################################## | 100% 
cmocean-2.0          | 178 KB    | ######################################################################## | 100% 
packaging-21.3       | 36 KB     | ######################################################################## | 100% 
pyyaml-6.0           | 178 KB    | ######################################################################## | 100% 
setuptools-62.2.0    | 1.3 MB    | ######################################################################## | 100% 
pandas-1.4.2         | 12.5 MB   | #############################################9                           |  64% 
bleach-5.0.0         | 123 KB    | ######################################################################## | 100% 
libgomp-12.1.0       | 459 KB    | ######################################################################## | 100% 
nspr-4.32            | 233 KB    | ######################################################################## | 100% 
libstdcxx-ng-12.1.0  | 4.3 MB    | ######################################################################## | 100% 
c-ares-1.18.1        | 113 KB    | ######################################################################## | 100% 
pexpect-4.8.0        | 47 KB     | ######################################################################## | 100% 
libgfortran-ng-12.1. | 23 KB     | ######################################################################## | 100% 
xorg-libxau-1.0.9    | 13 KB     | ######################################################################## | 100% 
libvorbis-1.3.7      | 280 KB    | ######################################################################## | 100% 
wcwidth-0.2.5        | 33 KB     | ######################################################################## | 100% 
libclang13-14.0.3    | 10.6 MB   | ######################################################1                  |  75% 
nbconvert-6.5.0      | 6 KB      | ######################################################################## | 100% 
notebook-shim-0.1.0  | 15 KB     | ######################################################################## | 100% 
tornado-6.1          | 657 KB    | ######################################################################## | 100% 
webencodings-0.5.1   | 12 KB     | ######################################################################## | 100% 
_libgcc_mutex-0.1    | 3 KB      | ######################################################################## | 100% 
libwebp-base-1.2.2   | 824 KB    | ######################################################################## | 100% 
fonts-conda-ecosyste | 4 KB      | ######################################################################## | 100% 
pyzmq-22.3.0         | 512 KB    | ######################################################################## | 100% 
hdf5-1.12.1          | 3.5 MB    | ######################################################################## | 100% 
argon2-cffi-21.3.0   | 15 KB     | ######################################################################## | 100% 
libevent-2.1.10      | 1.1 MB    | ######################################################################## | 100% 
python_abi-3.10      | 4 KB      | ######################################################################## | 100% 
importlib-metadata-4 | 33 KB     | ######################################################################## | 100% 
libsndfile-1.0.31    | 602 KB    | ######################################################################## | 100% 
colorspacious-1.1.2  | 30 KB     | ######################################################################## | 100% 
munkres-1.1.4        | 12 KB     | ######################################################################## | 100% 
backcall-0.2.0       | 13 KB     | ######################################################################## | 100% 
pytz-2022.1          | 242 KB    | ######################################################################## | 100% 
pandocfilters-1.5.0  | 11 KB     | ######################################################################## | 100% 
stack_data-0.2.0     | 21 KB     | ######################################################################## | 100% 
libllvm14-14.0.3     | 35.2 MB   | ################3                                                        |  23% 
fonts-conda-forge-1  | 4 KB      | ######################################################################## | 100% 
libiconv-1.16        | 1.4 MB    | ######################################################################## | 100% 
jedi-0.18.1          | 995 KB    | ######################################################################## | 100% 
urllib3-1.26.9       | 100 KB    | ######################################################################## | 100% 
jupyter_core-4.10.0  | 81 KB     | ######################################################################## | 100% 
beautifulsoup4-4.11. | 96 KB     | ######################################################################## | 100% 
argon2-cffi-bindings | 34 KB     | ######################################################################## | 100% 
pycparser-2.21       | 100 KB    | ######################################################################## | 100% 
font-ttf-dejavu-sans | 388 KB    | ######################################################################## | 100% 
python-fastjsonschem | 243 KB    | ######################################################################## | 100% 
libopus-1.3.1        | 255 KB    | ######################################################################## | 100% 
babel-2.10.1         | 6.7 MB    | ######################################################################## | 100% 
backports.functools_ | 9 KB      | ######################################################################## | 100% 
libtiff-4.3.0        | 638 KB    | ######################################################################## | 100% 
font-ttf-inconsolata | 94 KB     | ######################################################################## | 100% 
importlib_metadata-4 | 4 KB      | ######################################################################## | 100% 
pure_eval-0.2.2      | 14 KB     | ######################################################################## | 100% 
giflib-5.2.1         | 77 KB     | ######################################################################## | 100% 
unicodedata2-14.0.0  | 496 KB    | ######################################################################## | 100% 
cftime-1.6.0         | 220 KB    |                                                                          |   0% 
fonttools-4.33.3     | 1.6 MB    |                                                                          |   0% 
jupyter_client-7.3.1 | 90 KB     |                                                                          |   0% 
libdeflate-1.10      | 77 KB     |                                                                          |   0% 
debugpy-1.6.0        | 2.0 MB    |                                                                          |   0% 
nbconvert-pandoc-6.5 | 4 KB      |                                                                          |   0% 
pyparsing-3.0.9      | 79 KB     |                                                                          |   0% 
parso-0.8.3          | 69 KB     |                                                                          |   0% 
openjpeg-2.4.0       | 444 KB    |                                                                          |   0% 
libwebp-1.2.2        | 85 KB     |                                                                          |   0% 
jpeg-9e              | 268 KB    |                                                                          |   0% 
libcap-2.51          | 85 KB     |                                                                          |   0% 
jupyterlab_pygments- | 17 KB     |                                                                          |   0% 
typing_extensions-4. | 27 KB     |                                                                          |   0% 
ca-certificates-2021 | 139 KB    |                                                                          |   0% 
idna-3.3             | 55 KB     |                                                                          |   0% 
libbrotlicommon-1.0. | 65 KB     |                                                                          |   0% 
curl-7.83.1          | 89 KB     |                                                                          |   0% 
libev-4.33           | 104 KB    |                                                                          |   0% 
toml-0.10.2          | 18 KB     |                                                                          |   0% 
cryptography-36.0.2  | 1.6 MB    |                                                                          |   0% 
json-c-0.15          | 274 KB    |                                                                          |   0% 
lz4-c-1.9.3          | 179 KB    |                                                                          |   0% 
pyrsistent-0.18.1    | 92 KB     |                                                                          |   0% 
executing-0.8.3      | 18 KB     |                                                                          |   0% 
ipython_genutils-0.2 | 21 KB     |                                                                          |   0% 
ipykernel-6.13.0     | 187 KB    |                                                                          |   0% 
requests-2.27.1      | 53 KB     |                                                                          |   0% 
wheel-0.37.1         | 31 KB     |                                                                          |   0% 
charset-normalizer-2 | 35 KB     |                                                                          |   0% 
liblapack-3.9.0      | 12 KB     |                                                                          |   0% 
pyshp-2.3.0          | 862 KB    |                                                                          |   0% 
sqlite-3.38.5        | 1.5 MB    |                                                                          |   0% 
pthread-stubs-0.4    | 5 KB      |                                                                          |   0% 
fftw-3.3.10          | 6.4 MB    |                                                                          |   0% 
freetype-2.10.4      | 890 KB    |                                                                          |   0% 
pyqt-5.15.4          | 6.1 MB    |                                                                          |   0% 
hdf4-4.2.15          | 950 KB    |                                                                          |   0% 
send2trash-1.8.0     | 17 KB     |                                                                          |   0% 
pysocks-1.7.1        | 28 KB     |                                                                          |   0% 
zstd-1.5.2           | 458 KB    |                                                                          |   0% 
libbrotlienc-1.0.9   | 287 KB    |                                                                          |   0% 
matplotlib-3.5.2     | 6 KB      |                                                                          |   0% 
libcups-2.3.3        | 4.6 MB    |                                                                          |   0% 
libpq-14.3           | 3.0 MB    |                                                                          |   0% 
mysql-common-8.0.29  | 1.8 MB    |                                                                          |   0% 
libzip-1.8.0         | 126 KB    |                                                                          |   0% 
jsonschema-4.5.1     | 57 KB     |                                                                          |   0% 
jinja2-3.1.2         | 99 KB     |                                                                          |   0% 
libuuid-2.32.1       | 28 KB     |                                                                          |   0% 
keyutils-1.6.1       | 115 KB    |                                                                          |   0% 
nbformat-5.4.0       | 104 KB    |                                                                          |   0% 
decorator-5.1.1      | 12 KB     |                                                                          |   0% 
font-ttf-ubuntu-0.83 | 1.9 MB    |                                                                          |   0% 
ncurses-6.3          | 1002 KB   |                                                                          |   0% 
matplotlib-base-3.5. | 7.4 MB    |                                                                          |   0% 
numpy-1.22.3         | 6.8 MB    |                                                                          |   0% 
jupyterlab-3.4.1     | 6.0 MB    |                                                                          |   0% 
zeromq-4.3.4         | 351 KB    |                                                                          |   0% 
flit-core-3.7.1      | 44 KB     |                                                                          |   0% 
fontconfig-2.14.0    | 305 KB    |                                                                          |   0% 
nbclient-0.6.3       | 65 KB     |                                                                          |   0% 
nest-asyncio-1.5.5   | 9 KB      |                                                                          |   0% 
lcms2-2.12           | 443 KB    |                                                                          |   0% 
asttokens-2.0.5      | 21 KB     |                                                                          |   0% 
libgcc-ng-12.1.0     | 940 KB    |                                                                          |   0% 
traitlets-5.2.0      | 84 KB     |                                                                          |   0% 
libtool-2.4.6        | 511 KB    |                                                                          |   0% 
sniffio-1.2.0        | 16 KB     |                                                                          |   0% 
nbconvert-core-6.5.0 | 425 KB    |                                                                          |   0% 
libclang-14.0.3      | 127 KB    |                                                                          |   0% 
cycler-0.11.0        | 10 KB     |                                                                          |   0% 
bzip2-1.0.8          | 484 KB    |                                                                          |   0% 
libogg-1.3.4         | 206 KB    |                                                                          |   0% 
backports-1.0        | 4 KB      |                                                                          |   0% 
gst-plugins-base-1.2 | 2.8 MB    |                                                                          |   0% 
mistune-0.8.4        | 54 KB     |                                                                          |   0% 
defusedxml-0.7.1     | 23 KB     |                                                                          |   0% 
libgfortran5-12.1.0  | 1.8 MB    |                                                                          |   0% 
websocket-client-1.3 | 41 KB     |                                                                          |   0% 
brotli-1.0.9         | 18 KB     |                                                                          |   0% 
libssh2-1.10.0       | 233 KB    |                                                                          |   0% 
ld_impl_linux-64-2.3 | 667 KB    |                                                                          |   0% 
libpng-1.6.37        | 306 KB    |                                                                          |   0% 
libdb-6.2.32         | 23.3 MB   |                                                                          |   0% 
nss-3.77             | 2.1 MB    |                                                                          |   0% 
six-1.16.0           | 14 KB     |                                                                          |   0% 
kiwisolver-1.4.2     | 75 KB     |                                                                          |   0% 
qt-main-5.15.3       | 62.2 MB   |                                                                          |   0% 
nbclassic-0.3.7      | 14 KB     |                                                                          |   0% 
zipp-3.8.0           | 12 KB     |                                                                          |   0% 
pcre-8.45            | 253 KB    |                                                                          |   0% 
_openmp_mutex-4.5    | 23 KB     |                                                                          |   0% 
tk-8.6.12            | 3.3 MB    |                                                                          |   0% 
libnetcdf-4.8.1      | 1.5 MB    |                                                                          |   0% 
libcblas-3.9.0       | 12 KB     |                                                                          |   0% 
expat-2.4.8          | 187 KB    |                                                                          |   0% 
libcurl-7.83.1       | 342 KB    |                                                                          |   0% 
libffi-3.4.2         | 57 KB     |                                                                          |   0% 
libopenblas-0.3.20   | 10.1 MB   |                                                                          |   0% 
matplotlib-inline-0. | 11 KB     |                                                                          |   0% 
pyproj-3.3.1         | 503 KB    |                                                                          |   0% 
yaml-0.2.5           | 87 KB     |                                                                          |   0% 
pickleshare-0.7.5    | 9 KB      |                                                                          |   0% 
pip-22.1             | 1.6 MB    |                                                                          |   0% 
libnsl-2.0.0         | 31 KB     |                                                                          |   0% 
xarray-2022.3.0      | 650 KB    |                                                                          |   0% 
jbig-2.1             | 43 KB     |                                                                          |   0% 
proj-9.0.0           | 3.0 MB    |                                                                          |   0% 
prompt-toolkit-3.0.2 | 252 KB    |                                                                          |   0% 
netcdf4-1.5.8        | 2.7 MB    |                                                                          |   0% 
ipython-8.3.0        | 1.1 MB    |                                                                          |   0% 
brotlipy-0.7.0       | 342 KB    |                                                                          |   0% 
pillow-9.1.0         | 45.0 MB   |                                                                          |   0% 
soupsieve-2.3.1      | 33 KB     |                                                                          |   0% 
xz-5.2.5             | 343 KB    |                                                                          |   0% 

[Errno 122] Disk quota exceeded

```


### May 5, 2022
- [digital onboarding](https://uwnetid.sharepoint.com/:w:/s/og_uwt_psi/EVvo8B4kq-hEi8fhux-H8NoB9__ejxN6n_OTlhsWneHbPQ?e=CDRF77)
	- Reciprocal Shared calendar? 
	- Installed [Husky OnNet VPN](https://itconnect.uw.edu/connect/uw-networks/about-husky-onnet/use-husky-onnet/), or BIG-IP Edge Client.app
	- What will I use Eduroam and OnNet VPN for? 


**From Stefano's email**
1) [DO by the numbers](https://uwnetid.sharepoint.com/:w:/r/sites/og_uwt_psi/Shared%20Documents/SSMC/Bounding_Scenarios/MWQ_flowchart_SSM_ImpairedDO/Internal_Memo_Understanding__modelled%20DO_20220309_Clean_RM.docx?d=wf84e418e96794c10b3892d4f07a3b785&csf=1&web=1&e=UwMxNI)
2) Get familiar with the “bounding Scenarios folder and plots presented in a few specific presentations in the following order:
..\UW\UWT PSI - Documents\SSMC\Bounding_Scenarios\
- 2a. 20220426a_SSConference_SM_toshare.pdf
- 2b. 20210818_CoT_Task2_WWTP_Scenarios.pptx
- 2c. video folder- view files 
3) Have a look at [this summary of plots that were put in the SoK (some overlap)](
https://uwnetid.sharepoint.com/:p:/s/og_uwt_psi-MarineWaterQualityImplementationStrategy/EUKyVNDODSROsmOlopgxEkABu5MrNmK0SaET-9AVPBzzhw?email=rdmseas%40uw.edu&e=a6v253)

### May 4, 2022
- [DOE email lists](https://public.govdelivery.com/accounts/WAECY/subscriber/topics?utf8=✓&commit=Finish) 
- [Nitrogen in Puget Sound](https://waecy.maps.arcgis.com/apps/MapSeries/index.html?appid=907dd54271f44aa0b1f08efd7efc4e30)
- Asana expectations?
- Add [apendices for optimization](https://www.ezview.wa.gov/DesktopDefault.aspx?alias=1964&pageid=37106) in [shared folder](https://uwnetid.sharepoint.com/sites/og_uwt_psi/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2Fog%5Fuwt%5Fpsi%2FShared%20Documents%2FDO%20%2D%20KC%20%26%20CWA%2F3%2E%20Model%20Evaluation%20Group%2FEXTERNAL%2FModel%20Evaluation%20Group%20Collaboration%2FBackground%20%26%20Reference&p=true&ct=1651600887124&or=Teams%2DHL&ga=1)
- Vital sign development for Primary Production and Phytoplankton
