In here are scripts that run through the analysis workflow to recreate a lot
of the information used to create PSI's Whidbey report, restricted to Ecology's
baseline and reference runs used in their 2021
[Phase 1 Optimization Scenarios](https://www.ezview.wa.gov/Portals/_1962/Documents/PSNSRP/TechMemoPSNSRPOptimizationScenariosPhase1.pdf)
technical memorandum.

Start by editing the case file to match paths in your setup. You will need:

 * the model run outputs;
 * the freshwater boundary condition files
[cequalicm_wq_2014_Exist3_v3.dat](https://fortress.wa.gov/ecy/ezshare/EAP/SalishSea/OptimizationScenarios/model_input/2014/cequalicm_wq_2014_Exist3_v3.dat)
   and [cequalicm_wq_2014_ref3.dat](https://fortress.wa.gov/ecy/ezshare/EAP/SalishSea/OptimizationScenarios/model_input/2014/cequalicm_wq_2014_ref3.dat);
 * and the shapefile that describes each tracer element's area, volume, region,
   Part A DO standard, and masked status.

Set the paths to these files either in the .yaml file directly, or via the
iPython notebook which will do a bit of validation of the setup. By default,
all outputs will be added to subdirectories of where you run the scripts.

Make sure you have your conda environment set up.

Finally, edit each script's initial variables and paths to make sure they
match your file organization, then run them. `1_extract.sh` must be run first,
but for the others the order is not so important. All are set up to be run
either as a SLURM batch file or on the command line directly.
