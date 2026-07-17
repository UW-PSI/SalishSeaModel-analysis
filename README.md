# Salish Sea Model analysis at Puget Sound Institute 

This repository contains a collection of post-processing files designed to
create tables, graphics, and movies from Salish Sea Model output. This work
was funded by King County.

The most current version of the PSI code supports computing the Metabolic
index for three species across Puget Sound and the Straits.

this also includes and integrates the majority of code used to produce the
Disolved oxyen metryics for the regional sensitivty analesis for Northern Bays
(including Bellingham), Whidbey, and Main Basin (Lead contributor of code
Racheal Mueller with more recent updates by Ben Roberts and Stefano Mazzilli).
See [the original code](releases/tag/v1.1) which contains detailed
explanations.

![SSM Node map](graphics/NodeMap_All_ECYcolors.png)

## General Organization

The directory [py\_scripts](py_scripts/) contains all of the low-level
processing code in the form of Python scripts that can be executed on the
command line. The required Python environment is defined in
[environment.yml](environment.yml). Most intensive computation is handled
by the package [ssm\_utils](py_scripts/ssm_utils/). [Unit tests](tests/)
mostly apply to this package. Some extra one-off investigative or debugging
code is in the form of [Jupyter notebooks](notebooks/) although much of
this is out-of-date.

Python scripts generally read a YAML-formatted case file to know where
various dependencies can be found and the values of certain critical
parameters. The scripts are usually best executed via shell scripts to
assemble a full post-processing workflow; full examples of such workflows
can be found in [examples](examples/), including [for our latest metabolic
index study](examples/metabolic_index/).

The code requires two additional components which are not published here:
some [shapefiles](https://ww.github.com/UW-PSI/SalishSeaModel-grid)
(private repository) that define the Salish Sea Model and 303(d) grid
geometries, and the `process_netcdf.py` script for making the first
intermediate extractions from various formats of SSM NetCDF output files.
Please contact us at smazzilli@uw.edu if you would like to collaborate with
our work and receive these extra components to build your own complete
post-processing workflows.

## License and Copyright

All contents in this repository copyright (c) 2022-2026 by University of
Washington and created by Rachael D. Mueller/Ben Roberts (unless otherwise
specified) in collaboration with the [Project
Contributors](docs/CONTRIBUTORS.rst) at the [University of Washington's
Puget Sound Institute](https://www.pugetsoundinstitute.org). This work was
funded by King County.
