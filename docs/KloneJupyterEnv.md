# Creating a Jupyterlab environment on klone

## Install Miniconda
Refer to [Miniconda instructions](https://hyak.uw.edu/docs/tools/python/)
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
```
In my case, `$HOME` is set to `/mmfs1/home/rdmseas`
The `Klone` website linked above reccomends creating an environment in one's lab directory because "We discourage using your home directory as you will likely hit your inode (i.e., file) limits."  I have asked where our lab directory is, but I haven't gotten a straight answer, so I've experimented.  First, I tried `/gscratch/ssmc/USRS/PSI/Rachael/miniconda3/` 

Loading module
```
$module load foster/python/miniconda/3.8
```
Updating bash profile
```
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

Next: keep miniconda3 deactivated until called
```
conda config --set auto_activate_base false
```
use `conda activate` before each use and unload it with `conda deactivate`

## Create a miniconda environment for Jupyterlab using a .yml file
Creating a working environment when creating collaborative code is important because it makes it easier for everyone to get on the same platform for code development.  An extra step is to specify package versions (to ensure that the same package versions are being used as those used for code development).  I don't specify packages here because I want to be able to update and refresh to ensure that code functionality stays up-to-date with package upgrades.  

To start with, create a yaml file in a format similar to the below.  Packages need to be tailored to those that will be used.  Obviously, the jupyterlab part is important here. This is geared toward a generic setup but, environments can be specific to code package.  

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
```

Go through the following steps to create a Jupyterlab environment from the above `.yaml` file.
```
$ cd yaml-file-directory
$ module load foster/python/miniconda/3.8
$ conda env create -f ./klone-jupyter.yml
```
In my case, yaml-file-directory was `/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/envs`
 
The output looked like:
```
Collecting package metadata (repodata.json): done
Solving environment: done


==> WARNING: A newer version of conda exists. <==
  current version: 4.10.3
  latest version: 4.12.0

Please update conda by running

    $ conda update -n base -c defaults conda
Downloading and Extracting Packages
sip-6.5.1            | 373 KB    | ######################################################################## | 100%
...[MANY MORE PACKAGES LATER]...
[Errno 122] Disk quota exceeded
```
I ran into the same problem when installing from `/gscratch/ssmc/USRS/PSI/Rachael/envs`


