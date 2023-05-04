************************
Salish Sea Model analysis at Puget Sound Institute 
************************
This repository contains a collection of post-processing files designed to create tables, graphics, and movies from Salish Sea Model output. I was hired to run existing scripts to create baseline graphics and then develop more advanced analysis methods; however, the scripts weren't provided, so I developed my own.  The system I created relies on `bash scripts` running `SLURM arrays` that facilitate batch processing of multiple runs.  In addition, I use `.yaml` configuration files to organizing file paths and run information as well as a `shapefile` as the source of information for each model node (e.g. depth, region name, etc). The shapefile was developed by Kevin Bogue and is version controled in a different repository (`SalishSeaModel-grid` in [UW-PSI](https://github.com/UW-PSI/)).  

See `Project Contributors`_ for a list of those who have contributed to this system and `Cookbook`_ for recipes on how to use the files in this repository to cook up graphics, tables, and movies.   

Licenses
========
:License: Apache License, Version 2.0

All contents in this repository copyright 2022 by Rachael Mueller and the `Project Contributors`_ at `University of Washington`_.  They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.  Also, please cite Rachael Mueller and this repository if using or adapting any of this work in publications, presentations, or reports. 



.. _Project Contributors: https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst
.. _University of Washington: https://www.pugetsoundinstitute.org
.. _Cookbook: https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/creating_graphics_movies.md
