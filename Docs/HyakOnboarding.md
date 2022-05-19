# Hyak storage

`$HOME`  is located at `/mmfs1/home/USERID/` and has the most limited storage, at 10 GB.  
The "research lab" directory is located at `/mmfs1/gscratch/ssmc/`.  Sub-directories of this root-directory are the best places for installing miniconda3 environments and storing data. 
SSMC has a disk quota of 92 TB and has used (as of this file creation) 60 TB.  This storage is communal.  

Use command `hyakstorage` to get more information on `home` and `"research lab"` storage

# Install Miniconda3 in lab workspace
We install miniconda in the lab workspace because there isn't enough disk space to accomodate miniconda environments in `$HOME`.  See [Hyak Miniconda3 instructions](https://hyak.uw.edu/docs/tools/python/) for more details.  

Navigate to lab workspace
```
$ cd /mmfs1/gscratch/ssmc/PSI/
```
create a personal folder and change directory to this directory
```
$ mkdir your-personal-folder-name
$ cd your-personal-folder-name
```
Download miniconda3 in this directory
```
$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```
The output will look something like: 
```
--2022-05-19 10:14:24--  https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
Resolving repo.anaconda.com (repo.anaconda.com)... 104.16.131.3, 104.16.130.3, 2606:4700::6810:8303, ...
Connecting to repo.anaconda.com (repo.anaconda.com)|104.16.131.3|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 76607678 (73M) [application/x-sh]
Saving to: ‘Miniconda3-latest-Linux-x86_64.sh’

Miniconda3-latest-L 100%[===================>]  73.06M   232MB/s    in 0.3s    

2022-05-19 10:14:25 (232 MB/s) - ‘Miniconda3-latest-Linux-x86_64.sh’ saved [76607678/76607678]
```
Install miniconda3 to this directory
```
$ bash Miniconda3-latest-Linux-x86_64.sh -b -p ./miniconda3
```
My output looked like:
```
PREFIX=/mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3
Unpacking payload ...
Collecting package metadata (current_repodata.json): done                       
Solving environment: done

## Package Plan ##

  environment location: /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/miniconda3

  added / updated specs:
    - _libgcc_mutex==0.1=main
    - _openmp_mutex==4.5=1_gnu
    - brotlipy==0.7.0=py39h27cfd23_1003
    - ca-certificates==2022.3.29=h06a4308_1
    - certifi==2021.10.8=py39h06a4308_2
    - cffi==1.15.0=py39hd667e15_1
    - charset-normalizer==2.0.4=pyhd3eb1b0_0
    - colorama==0.4.4=pyhd3eb1b0_0
    - conda-content-trust==0.1.1=pyhd3eb1b0_0
    - conda-package-handling==1.8.1=py39h7f8727e_0
    - conda==4.12.0=py39h06a4308_0
    - cryptography==36.0.0=py39h9ce1e76_0
    - idna==3.3=pyhd3eb1b0_0
    - ld_impl_linux-64==2.35.1=h7274673_9
    - libffi==3.3=he6710b0_2
    - libgcc-ng==9.3.0=h5101ec6_17
    - libgomp==9.3.0=h5101ec6_17
    - libstdcxx-ng==9.3.0=hd4cf53a_17
    - ncurses==6.3=h7f8727e_2
    - openssl==1.1.1n=h7f8727e_0
    - pip==21.2.4=py39h06a4308_0
    - pycosat==0.6.3=py39h27cfd23_0
    - pycparser==2.21=pyhd3eb1b0_0
    - pyopenssl==22.0.0=pyhd3eb1b0_0
    - pysocks==1.7.1=py39h06a4308_0
    - python==3.9.12=h12debd9_0
    - readline==8.1.2=h7f8727e_1
    - requests==2.27.1=pyhd3eb1b0_0
    - ruamel_yaml==0.15.100=py39h27cfd23_0
    - setuptools==61.2.0=py39h06a4308_0
    - six==1.16.0=pyhd3eb1b0_1
    - sqlite==3.38.2=hc218d9a_0
    - tk==8.6.11=h1ccaba5_0
    - tqdm==4.63.0=pyhd3eb1b0_0
    - tzdata==2022a=hda174b7_0
    - urllib3==1.26.8=pyhd3eb1b0_0
    - wheel==0.37.1=pyhd3eb1b0_0
    - xz==5.2.5=h7b6447c_0
    - yaml==0.2.5=h7b6447c_0
    - zlib==1.2.12=h7f8727e_1


The following NEW packages will be INSTALLED:

  _libgcc_mutex      pkgs/main/linux-64::_libgcc_mutex-0.1-main
  _openmp_mutex      pkgs/main/linux-64::_openmp_mutex-4.5-1_gnu
  brotlipy           pkgs/main/linux-64::brotlipy-0.7.0-py39h27cfd23_1003
  ca-certificates    pkgs/main/linux-64::ca-certificates-2022.3.29-h06a4308_1
  certifi            pkgs/main/linux-64::certifi-2021.10.8-py39h06a4308_2
  cffi               pkgs/main/linux-64::cffi-1.15.0-py39hd667e15_1
  charset-normalizer pkgs/main/noarch::charset-normalizer-2.0.4-pyhd3eb1b0_0
  colorama           pkgs/main/noarch::colorama-0.4.4-pyhd3eb1b0_0
  conda              pkgs/main/linux-64::conda-4.12.0-py39h06a4308_0
  conda-content-tru~ pkgs/main/noarch::conda-content-trust-0.1.1-pyhd3eb1b0_0
  conda-package-han~ pkgs/main/linux-64::conda-package-handling-1.8.1-py39h7f8727e_0
  cryptography       pkgs/main/linux-64::cryptography-36.0.0-py39h9ce1e76_0
  idna               pkgs/main/noarch::idna-3.3-pyhd3eb1b0_0
  ld_impl_linux-64   pkgs/main/linux-64::ld_impl_linux-64-2.35.1-h7274673_9
  libffi             pkgs/main/linux-64::libffi-3.3-he6710b0_2
  libgcc-ng          pkgs/main/linux-64::libgcc-ng-9.3.0-h5101ec6_17
  libgomp            pkgs/main/linux-64::libgomp-9.3.0-h5101ec6_17
  libstdcxx-ng       pkgs/main/linux-64::libstdcxx-ng-9.3.0-hd4cf53a_17
  ncurses            pkgs/main/linux-64::ncurses-6.3-h7f8727e_2
  openssl            pkgs/main/linux-64::openssl-1.1.1n-h7f8727e_0
  pip                pkgs/main/linux-64::pip-21.2.4-py39h06a4308_0
  pycosat            pkgs/main/linux-64::pycosat-0.6.3-py39h27cfd23_0
  pycparser          pkgs/main/noarch::pycparser-2.21-pyhd3eb1b0_0
  pyopenssl          pkgs/main/noarch::pyopenssl-22.0.0-pyhd3eb1b0_0
  pysocks            pkgs/main/linux-64::pysocks-1.7.1-py39h06a4308_0
  python             pkgs/main/linux-64::python-3.9.12-h12debd9_0
  readline           pkgs/main/linux-64::readline-8.1.2-h7f8727e_1
  requests           pkgs/main/noarch::requests-2.27.1-pyhd3eb1b0_0
  ruamel_yaml        pkgs/main/linux-64::ruamel_yaml-0.15.100-py39h27cfd23_0
  setuptools         pkgs/main/linux-64::setuptools-61.2.0-py39h06a4308_0
  six                pkgs/main/noarch::six-1.16.0-pyhd3eb1b0_1
  sqlite             pkgs/main/linux-64::sqlite-3.38.2-hc218d9a_0
  tk                 pkgs/main/linux-64::tk-8.6.11-h1ccaba5_0
  tqdm               pkgs/main/noarch::tqdm-4.63.0-pyhd3eb1b0_0
  tzdata             pkgs/main/noarch::tzdata-2022a-hda174b7_0
  urllib3            pkgs/main/noarch::urllib3-1.26.8-pyhd3eb1b0_0
  wheel              pkgs/main/noarch::wheel-0.37.1-pyhd3eb1b0_0
  xz                 pkgs/main/linux-64::xz-5.2.5-h7b6447c_0
  yaml               pkgs/main/linux-64::yaml-0.2.5-h7b6447c_0
  zlib               pkgs/main/linux-64::zlib-1.2.12-h7f8727e_1


Preparing transaction: done
Executing transaction: done
installation finished.
```
Initialize `bash` shell

```
$ module load foster/python/miniconda/3.8
$ conda init bash
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
Log out and log back in. Now `(base)` shows up at the base of terminal, indicated that miniconda3 is active.

Next: keep miniconda3 deactivated until called
```
conda config --set auto_activate_base false
```
use `conda activate` before each use and unload it with `conda deactivate`

# create a miniconda environment using a Yaml file
Yaml files are great because they use a data-oriented language structure that allows for useful, easy-for-humans-to-read structure that is also machine readable. 

Create a `envs` folder to contain environment.yaml files
```
$ mkdir envs
```
Add Yaml file to `envs` directory.  Mine is called `klone-jupyter.yml` and includes packages that I anticipate needing to use for my project.  The nice thing about using a Yaml file for creating an environment is that there is a clear record of the packages used and the file can be modified down the road, as needed.  This is what I have inside `klone-jupyter.yml`.
```
$ more klone-jupyter.yml 
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
One might think that installing from this `envs` folder would install the environment in the lab directory after having installed `miniconda3` to the lab directory; however, this isn't the case.  The environment will still be installed to $HOME/.conda.  A symlink needs to be created in order to point `conda` from this location to the desired lab directory locations.  The solution is burried in the responses to this question on [Stack Overflow](https://stackoverflow.com/questions/37926940/how-to-specify-new-environment-location-for-conda-create).  This symlink is established as follows:

```
ln -s /mmfs1/gscratch/ssmc/USRS/PSI/Rachael/.conda $HOME/.conda
```
From within `envs` folder, we can install this environment as follows
```
$ module load foster/python/miniconda/3.8
$ conda env create -f ./klone-jupyter.yml
```
It took a while (~10 minutes) to get through `Solving environment:` mode.  Afterwards, the environment packages and versions were listed out.  The list looked like:
```
$ conda env create -f ./klone-jupyter.yml
Collecting package metadata (repodata.json): done
Solving environment: done


==> WARNING: A newer version of conda exists. <==
  current version: 4.10.3
  latest version: 4.12.0

Please update conda by running

    $ conda update -n base -c defaults conda



Downloading and Extracting Packages
freetype-2.10.4      | 890 KB    | ##################################### | 100% 
tornado-6.1          | 657 KB    | ##################################### | 100% 
...[and many more!]...
```

My output looks like

# `.bashrc` setup
Useful aliases for `.bashrc` file
...
