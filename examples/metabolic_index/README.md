# Metabolic Index Computation Framework - Initial Release

To run this code, a Linux or possibly Mac OS X environment is needed. Windows Subsystem for Linux (WSL) should work fine also.

Begin by installing an Anaconda distribution. We recommend [miniforge](https://github.com/conda-forge/miniforge).

Next, set up the included conda environment with the command `conda env create -f environment.yml`

# Running the Workflow

All the code is kept in the directory `py_scripts` and the unit tests are in
`tests`. This directory is the location from which to actually perform the
analysis, which can be copied out of the source tree before beginning.

You probably need to edit the file `paths.rc` to reflect your local setup.

Once your environment is set up, all that's required is to execute each of
the bash scripts in order. `0_run_tests.sh` simply runs the project's unit
tests and can be skipped. `1_extract.sh` is used to create intermediate
NetCDF files in the SSM\_data subdirectory containing dissolved oxygen,
temperature, and salinity data from the Salish Sea Model output files. If you
contact us to acquire those intermediate files, the full model outputs are
not necessary and this step can also be skipped.

The rest of the scripts are:
 * `2_DO_Saturation.sh`: Computes secondary oceanographic parameters needed for the metabolic index calculation: DO partial pressure and conservative temperature. This one takes a few minutes to run.
 * `3_calc_mi.sh`: Performs the metabolic index calculation for each species.
 * `4_plotting_tables.sh`: Runs a per-species analysis pipeline on the metabolic index results.
 * `5_daily_mi_plots_movies.sh`: Generates daily plots of depth-minimum MI for each species and
 assembles them into an animation using FFMPEG.
 * `6_exposure_return.sh`: Computes the duration of each exposure and net exposure, then computes
 statistics and generates planar plots.

More information about what each Python script does is described in
[running.md](../../docs/running.md).

Each script is set up with a header meant to be read by the SLURM job scheduler
on a compute cluster like UW's Hyak. One can also use that information to infer
about the code's speed, scalability and memory requirements for running on
other systems.
