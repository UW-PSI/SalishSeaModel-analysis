# Metabolic Index Computation Framework - Initial Release

To run this code, a Linux or possibly Mac OS X environment is needed. Windows Subsystem for Linux (WSL) should work fine also.

Begin by installing an Anaconda distribution. We recommend [miniforge](https://github.com/conda-forge/miniforge).

Next, set up the included conda environment with the command `conda env create -f environment.yml`

# Running the Code

All the code is kept in the directory `py_scripts` and the unit tests are in `tests`. The `run` directory is the location from which to actually perform the analysis.

So enter then `run` directory, and all that's required is to execute each of the bash scripts there in order, first making any environment-specific edits related to your conda instance. `0_run_tests.sh` simply runs the project's unit tests and can be skipped. `1_extract.sh` is used to create intermediate NetCDF files in the SSM_data subdirectory containing dissolved oxygen, temperature, and salinity data from the Salish Sea Model output files. If you contact us to acquire those intermediate files, the full model outputs are not necessary and this step can also be skipped.

The rest of the scripts are:
 * `2_AllParam_load.sh`: Performs some extra annotation on the intermediate netCDF files.
 * `3_DO_Saturation.sh`: Computes secondary oceanographic parameters needed for the metabolic index calculation: DO saturation, conservative temperature, absolute salinity. This one takes a while to run.
 * `4_calc_mi.sh`: Performs the metabolic index calculation for each species.
 * `5_plotting_tables.sh`: Runs a per-species analysis pipeline on the metabolic index results.

Each script is set up with a header meant to be read by the SLURM job scheduler on a compute cluster like UW's Hyak. One can also use that information to infer about the code's speed, scalability and memory requirements for running on other systems.