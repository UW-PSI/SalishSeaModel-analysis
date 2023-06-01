# Table of contents
1. [Introduction](#intro)
1. [Setup](#setup)
    1. [System requirements](#requirements)
    2. [Creating a configuration file](#configuration)
2. [Tables](#tables)
    1. [Nutrient loading by scenario based on model input files](#nutrientLoadingFromInputFile)
    2. [Regional information](#regionalInformation)
    3. [Non-compliance by region (days, volume, and percent volume)](#noncompliantTable)
    4. [Dissolved Oxygen below 2, 5, and DO standard by region](#threshold)
3. [Graphics](#graphics)
    1. [Time series of volume noncompliant](#noncompliantTS)
    2. [Noncompliance by region](#noncompliantDaysByRegion)
    3. [Normalized noncompliance vs. volume days](#noncompliance_vs_volumedays)
    4. [Nutrient Loadings (WWTP and rivers)](#nutrientLoading)
4. [Animations](#movies)
    1. [Salinity, N03, and/or DOXG (map-style)](#moviesConcentration)
    2. [Hypoxic cells (DO < 2 mg/l, map-style)](#moviesHypoxia)
    3. [Percent volume of cell that is hypoxic (DO < 2 mg/l, map-style)](#moviesPercentHypoxic)
    4. [Dissolved oxygen noncompliance (scenario - reference < -0.2 or -0.25)](#moviesNonComplaint)
5. [QAQC: Making sure there aren't problems with the inputs and outputs](#QAQC)
    1. [Nutrient loading inputs](#qaqc_loading)  
    2. [Model output](#qaqc_modeloutput)
6. [Reference links](#references)

# Introduction <a name="intro"></a>
The goal of this file is to provide an overview of the setup and resources required to develop the tables, graphics, and animations provided to King County for the evaluation of nutrient loading impacts. In all of these cases, I was provided with a list of runs to evaluate and was requested to create a particular kind of graphic.  Included here is documentation on the code used to create the products.  Some work more s    moothly than others.  They were on a development continuum when funds for the project ran out.  The data to create these graphics and tables are not included and would need to be provided by Stefano Mazzilli at Puget Sound Institute.  Please email [Rachael Mueller](mailto:RachaelDMueller@gmail.com) with comments, suggestions, and/or corrections to the code or documentation.  

# Setup <a name="setup"></a>
## Requirements <a name="requirements"></a>
1. A miniconda environment in which to run scripts and notebooks.  My miniconda environment file (jupyter-klone.yaml) looks like:
```
# virtualenv environment description for a useful jupyter
# environment on Klone
#
# Create a virtualenv containing these packages with:
#
#    module load foster/python/miniconda/3.8
#    conda env create -f /gscratch/ssmc/USRS/PSI/Rachael/envs/klone-jupyter.yml 
#
# To activate this environment use:
#    conda activate klone-jupyter
# 
# Deactivate with:
#    conda deactivate
#
# Delete environment using:
#    conda env remove -klone_jupyter
#

name: klone_jupyter

channels:
 - conda-forge
 - defaults

dependencies:
 - pyaml
 - cmocean
 - jupyterlab
 - matplotlib
 - scipy
 - cartopy
 - netCDF4
 - xarray
 - geopandas
```
2. An Apptainer "Container" in which to run FFMPEG.  See, FFMPEG section of [HyakOnboarding.md](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/HyakOnboarding.md#ffmpeg). 

## Create run configuration file <a name="configuration"></a>
1. Define run and model output file locations. 
2. Create [SSM_config_whidbey](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/etc/SSM_config_whidbey.ipynb) file with file paths and tag names for this set of model runs.

# Tables <a name="tables"></a>
## Nutrient loading by scenario based on model input files <a name="nutrientLoadingFromInputFile"></a>
I developed code to create a table of the total nitrogen loading for each scenario based on getting the values directly from input files. Thanks again to Ben Roberts for his help in understanding the file formats and providing better code than what I had cooked up in my first attempt at creating a solution!
I haven't yet developed the method into a script and relied on my [Table1_NutrientLoadings.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/Table1_NutrientLoadings.ipynb) notebook for creating the tables.

## Regional information <a name="regionalInformation"></a>
Questions were raised about the area, volume, depth, nitrogen sources, etc. for the different regions explored in this project, and I helped answer these questions with [Table2_RegionInformation.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/Table2_RegionInformation.ipynb) and the table it produces.  

## Create table of noncompliant (days, volume, and percent volume) <a name="noncompliantTable"></a>
The code for non-compliance uses a threshold value that can be passed in.  The default values for the `scenario - reference` difference is -0.25 mg/L, which is equivalent to the Department of Ecology (DOE) `rounding method` based on a -0.2 mg/L threshold.  See pp. 49 and 50 of Appendix F of [Optimization Report Appendix](https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf) for more details.  
1. Run [process_netcdf.py](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh) to generate minimum dissolved oxygen in water column and bottom level.  Select:
```
case = "whidbey"
param="DOXG"
stat_type="min"
```
The result is minimum, daily DO across all levels.  If separate NetCDF are wanted for surface and bottom minimum DO then add "1" to function call and these files will be produced as well, i.e.: `python ${py_path}/process_netcdf.py ${file_path} ${param} ${case} ${stat_type} 1 1`
The output for the minimum value across the entire water column (wc) will be output to the following subdirectory of `ssm['paths']['processed_output']` (in SSM_config_whidbey.ipynb):
```
whidbey/DOXG/[RUN_TAG]/wc/daily_min_DOXG_wc.nc
```
Replace `wc` above with `surface` and `bottom` for the paths to those files.

Note: Be sure to update the number of `slurm-arrays` used in bash scripts to match the number of scenarios.  There is no error-check in this bash script so not all output will be processed if there isn't a sufficient allocation of `slurm-arrays`. 

2. Run the [bash script for creating non-compliance table](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/calc_noncompliance.sh).  This bash script calls the python script [calc_noncompliance.py](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/py_scripts/calc_noncompliance.py)

## Create tables for calculating DO below 2, 5, and/or DO standard <a name="threshold"></a>
1. Change case to `whidbey` in `bash_scripts/calc_DO_below_threshold.sh`.  This is the only update needed between different cases, because I updated the code to eliminate need to specify reading `SSM_config_whidbey.yaml` by hard-coding in the use of `case` 
```
with open('../etc/SSM_config_{case}.yaml', 'r') as file:
   ssm = yaml.safe_load(file)
   # get shapefile path    
   shp = ssm['paths']['shapefile']
```
3. I updated code to to use `run_tag` dictionary (ssm['run_information']['run_tag'][`whidbey`]) for column names to eliminate need to modify code by hand. (Same upgrade as in `calc_DO_noncompliant.py`)

The runtime for creating these spreadsheets (using a slurm array over three nodes, one for each spreadsheet) is: ~16 minutes

File Reference:
- [calc_DO_below_threshold.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/calc_DO_below_threshold.sh)
- [calc_DO_below_threshold.py](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/py_scripts/calc_DO_below_threshold.py)

# Graphics <a name="graphics"></a>
## Create time series graphics for volume noncompliant <a name="noncompliantTS"></a>

### Individual time series <a name="noncompliantTS_individual"></a>
Updated [calc_noncompliant_timeseries.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/calc_noncompliance_timeseries.sh):
```
#SBATCH --array=0-9

case="whidbey"

run_folders=(
"wqm_baseline"
"wqm_reference"
"3b"
"3e"
"3f"
"3g"
"3h"
"3i"
"3l"
"3m"
)
script_path="/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/SalishSeaModel-analysis/py_scripts/"
```
Updated python script to assign .yaml file name by `case`:
```
with open(f'../etc/SSM_config_{case}.yaml', 'r') as file:
        ssm = yaml.safe_load(file)
        # get shapefile path    
        shp = ssm['paths']['shapefile']

```
It takes ~6 minutes of computing time to create the spreadsheets.

Similarly updated code for `plot_noncompliant_timeseries`, except the shell script for this function call requires `run_tag`:
```
run_tag=(
"baseline"
"reference"
"3b"
"3e"
"3f"
"3g"
"3h"
"3i"
"3l"
"3m"
)
```
It takes ~0.1 minutes of computing time to create the graphics.
### Multi-panel time series of noncompliance <a name="noncompliantTS_allruns"></a>
In the interest of time, I gave up one creating an adaptable script and instead modified the Jupyter Notebook [plot_noncompliance_timeseries.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/plot_noncompliance_timeseries.ipynb) for each regional application. 

An example of the resulting graphic is below: 
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/whidbey_Whidbey_noncompliant_m0p25_wc_TS.png" width="600" />


File Reference:
- [calc_noncompliance_timeseries.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/calc_noncompliance_timeseries.sh)
- [calc_noncompliance_timeseries.py](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/py_scripts/calc_noncompliance_timeseries.py)
- [plot_noncompliance_timeseries.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/plot_noncompliance_timeseries.ipynb)
Previously used:
- [plot_noncompliance_timeseries.py](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/py_scripts/plot_noncompliance_timeseries.py)
- [plot_5panel_noncompliant_timeseries.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/plot_5panel_noncompliant_timeseries.sh)
- [plot_5panel_noncompliant_timeseries.py](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/py_scripts/plot_5panel_noncompliant_timeseries.py)

## Number of noncompliant days for each region <a name="noncompliantDaysByRegion"></a>
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/whidbey_NoncompliantDaysByRegion_notext_reordered.png" width="600" />
This graphic was developed in [plot_noncompliant_days_by_Region.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/plot_noncompliant_days_by_Region.ipynb) by specifying case (SOG_NB, whidbey, main) and using tag names in configuration .yaml files. 

## Normalized volume non-compliance vs. nitrogen loading <a name="noncompliance_vs_volumedays"></a>
The method for creating this graphic evolved as I developed the ability to read loading quantities directly from the input files. The three regions and corresponding notebooks are: 
1. SOG ([plot_sog_loading_vs_noncompliance.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/plot_sog_loading_vs_noncompliance.ipynb))
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/sog_nitrogen_volumedays_ALL_REGIONS.png" width="400" />
2. Whidbey 
        1.[create_loading_spreadsheets_whidbey.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/create_loading_spreadsheets_whidbey.ipynb)
        2.[plot_whidbey_loading_vs_noncompliance.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/plot_whidbey_loading_vs_noncompliance.ipynb)
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/whidbey_nitrogen_volumedays_fit_Whidbey_2panel.png" width="600" />
3. Main ([create_loading_spreadsheets_main.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/create_loading_spreadsheets_main.ipynb))
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/main_nitrogen_volumedays_fit_Main_noline.png" width="300" />

## Nutrient Loading graphics <a name="nutrientLoading"></a>
These plots are still done in a Jupyter Notebook that requires quite a bit of manual editing. 
See [plot_nutrient_loading_whidbey.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/reports/plot_nutrient_loading_whidbey.ipynb).  Examples of the resulting graphics are shown below. Grey shading between the `2014` and `reference` conditions is used to highlight changes over time.

<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/whidbey_river_loadings.png" width="600" />
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/whidbey_WWTP_loadings.png" width="600" />

# Animations <a name="movies"></a>
All animations are created using the software `ffmpeg` through an Apptainer Container, on Hyak.  It wasn't obvious to me how to control the runtime, and I needed to do a bit of online searching and experimenting to figure out a solution.  What I found was that the `-r` flag didn't do anything.  The solution that worked for my setup was the `-framerate` flag, e.g.:
```
apptainer exec --bind ${graphics_dir} --bind ${output_dir} ~/ffmpeg.sif ffmpeg -start_number 6 -framerate 6 -i ${graphics_dir}${case}_${run_tags[${SLURM_ARRAY_TASK_ID}]}_${param}_${stat_type}_conc_${loc}_%d_whidbeyZoom.png -vcodec mpeg4 ${output_dir}${case}_${run_tags[${SLURM_ARRAY_TASK_ID}]}_${param}_${stat_type}_${loc}_whidbeyZoom.mp4
```
Here, I use `-framerate 6` to get a minute-long movie by incorporating 6 images per second from a pool of ~366 images.  Including `-vcodec mpeg4` was neeccessary for me to get the product to play on my macOS Monterey.  We ran into trouble playing the output on a PC and worked around this problem by saving to `.avi` before finding the problem was on the PC side.  In the process of troubleshooting, I also read that adding `-c:v libx264 -pix_fmt yuv420p` can make the `.mp4` more broadly accessible, but I haven't yet received confirmation that this is an important/neccessary specification.  
## Create NetCDF file for variable of interest
All animations require a NetCDF of whatever variable (DOXG, salinity, NO3, etc.) and statistic (min, max, mean, etc.) that is being represented.  Theses are created using: [process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh).  These NetCDF only have to be created once, but I include this as a first step for all movies listed below so that the instructions are "stand alone."  If this step is done for one movie it does not need to be repeated for another. [Process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh) saves desired concentration information to NetCDF files stored in `/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/{case}/{param}/{SCENARIO_NAME}/{LOC}` where:
    -  `{case}` is SOG_NB, whidbey or main,
    -  `{param}` is the SSM output parameter name (e.g. DOXG),
    -  `{SCENARIO_NAME}` is the run-tag used on HYAK (e.g. `3m`), and
    -  {LOC}` is either wc (water column), bottom, or surface. 

## Concentration (DO, salinity, NO3) <a name="moviesConcentration"></a>

1. [process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh): Creates a NetCDF of the model output that only includes information for the desired variable (e.g. `DOXG`).  A file is automatically created for all 3D values and can be created for surface-only and bottom-only values using the `surface_flag` and/or `bottom_flag` when calling [process_netcdf.py](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/py_scripts/process_netcdf.py).  Use [process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh) for a shell script to call `process_netcdf.py` with the desired setup. The way I have the file structure setup, the files are saved to, e.g.: 
`/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/{case}/{param}/{SCENARIO_NAME}/{LOC}` where:
    -  `{case}` is SOG_NB, whidbey or main,
    -  `{param}` is the SSM output parameter name (e.g. DOXG),
    -  `{SCENARIO_NAME}` is the run-tag used on HYAK (e.g. `3m`), and
    -  {LOC}` is either wc (water column), bottom, or surface. 
2. [plot_conc_graphics_for_movies.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/plot_conc_graphics_for_movies.sh): Uses output from [process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh) to create daily plots of concentration maps for either `FullDomain` or `Regional` view.  The `Regional` view uses region names in the shapefile and only plots the concentrations for the unmasked nodes within the given region.  The `FullDomain` graphics show values for masked and unmasked nodes. This script requires patience (~15 minutes). Daily graphics are saved to, e.g.:
```
/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/projects/KingCounty/data/whidbey/DOXG/concentration/movies/FullDomain/wc/3b/whidbey_3b_DOXG_min_conc_wc_1.png
```
3. [create_conc_movies.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/create_conc_movies.sh). Uses a FFMPEG apptainer to compile individual graphic outputs from `plot_conc_graphics_for_movies.sh` into a .mp4 movie.  This script goes quickly. There is an option `FullDomain` or `Region`.  The script will no over-write existing movies.

## Hypoxia (DO < 2 mg/l) <a name="moviesHypoxia"></a>
1. [process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh).  
2. [plot_threshold_movie.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/plot_threshold_movie.sh)
3. [create_DO_threshold_movie.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/create_DO_threshold_movie.sh)

## Percent Hypoxic <a name="moviesPercentHypoxic"></a>
1. [process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh)
2. [plot_percentVolumeHypoxic_movie.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/plot_percentVolumeHypoxic_movie.sh)
3. [create_percentHypoxic_movie.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/create_percentHypoxic_movie.sh)

## NonComplaint <a name="moviesNonComplaint"></a>
The code for non-compliance uses a threshold value that can be passed in.  The default values for the `scenario - reference` difference is -0.25 mg/L, which is equivalent to the Department of Ecology (DOE) `rounding method` based on a -0.2 mg/L threshold.  See pp. 49 and 50 of Appendix F of  [Optimization Report Appendix](https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/Appendices%20A-G%20for%20Tech%20Memo.pdf) for more details.
1. [process_netcdf.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/process_netcdf.sh)
2. [plot_NonCompliance_graphics4movie.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/plot_NonCompliance_graphics4movie.sh)
3. [create_noncompliance_movie.sh](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/bash_scripts/create_noncompliance_movie.sh)

# QAQC: Making sure there aren't problems with the inputs and outputs <a name="QAQC"></a>
## Nutrient loading inputs <a name="qaqc_loading"></a>  
Salish Sea Model nitrogen inputs are in units of concentration but some of our runs required altering loading.  In these runs, I needed to scale concentrations appropriately in order to accurately change the loading.  These graphics reflect my internal QAQC to ensure that I scaled the nitrogen levels correctly and as requested.  
1. Validating the nutrient input loadings for Main region: [validate_SSM_input_loading_main.ipynb]((https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/QAQC/validate_SSM_input_loading_main.ipynb)
2. Validating the nutrient input loadings for Whidbey region: [validate_SSM_input_loading.ipynb](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/notebooks/QAQC/validate_SSM_input_loading.ipynb)

## Model output <a name="qaqc_modeloutput"></a>
1. Histograms of DO difference between 2014 and scenario [QAQC_DeltaDO_DeltaNO3_MainRegion.ipynb](http://localhost:8800/lab/workspaces/auto-1/tree/PSI-analysis/notebooks/QAQC/QAQC_DeltaDO_DeltaNO3_MainRegion.ipynb).
2. Comparing normalized nitrogen loading to normalized noncompliance.  Other models that I've worked with have crashed when solutions become infinite but that's not the case with this version of ICM.  The way that I learned this was to notice outliers in plots that compare normalized noncompliance to normalized nitrogen.  See cases `Wtp1` (typo for `Mtp1`) and `Mtp2` in below figure. 
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/main_nitrogen_volumedays_fit_Main_noline_orig.png" width="400" />
A closer look revealed oxygen outputs that I recall being O(1e38), i.e. too high.  There were reported issues with MPI on the HPC at the time.  Su Kyong and I are suspicious that these high numbers are the result of a glitch in the parallel processing. Re-running the erroneous runs fixed the problem.  
<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/main_nitrogen_volumedays_fit_Main_noline.png" width="400" />
The concept for the graphic of normalized non-compliance to normalized nitrogen loading was introduced by Joel Baker and developed further here to separate out the cases where nitrogen loading is varied in WWTPs from those in which nitrogen is varied in river inputs.  


# References <a name="references"></a>
The following files are not public and require access permission through the Puget Sound Institute. 
1. [Municipal model runs and scripting task list.xlsx](https://uwnetid.sharepoint.com/:x:/r/sites/og_uwt_psi/Shared%20Documents/Nutrient%20Science/9.%20Modeling/Municipal%20%20model%20runs%20and%20scripting%20task%20list.xlsx?d=w417abadac06143409d092a23a26727e6&csf=1&web=1&e=tgJY69) (Internal PSI document)
2. [Whidbey configuration file](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/etc/SSM_config_whidbey.ipynb)
3. [Whidbey_Figures&Tables.xlsx](https://uwnetid.sharepoint.com/:x:/r/sites/og_uwt_psi/_layouts/15/Doc.aspx?sourcedoc=%7B9011F04E-F423-4B45-A0EA-75338168A1B3%7D&file=Whidbey_Figures%26Tables.xlsx&action=default&mobileredirect=true) (Internal PSI document)
4. [SOG_NB_Figures&Tables.xlsx](https://uwnetid.sharepoint.com/:x:/r/sites/og_uwt_psi/_layouts/15/Doc.aspx?sourcedoc=%7B3788B09C-126F-40BF-86AF-22DEC185E831%7D&file=SOG_NB_Figures%26Tables.xlsx&action=default&mobileredirect=true) (Internal PSI document)
5. [Main_Figures&Tables](https://uwnetid.sharepoint.com/:x:/r/sites/og_uwt_psi/Shared%20Documents/Nutrient%20Science/9.%20Modeling/7.3%20Main/Main_Figures%26Tables.xlsx?d=wa78a9065fcb640b488399c16db32def4&csf=1&web=1&e=V4z8Bd) (Internal PSI document)

