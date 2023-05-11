************************
Salish Sea Model analysis at Puget Sound Institute 
************************
This repository contains a collection of post-processing files designed to create tables, graphics, and movies from Salish Sea Model output.  My goal was to be strategic in code development so as to produce well-organized and efficient system; but I was hired onto this project when there was already an urgent need to produce results.  I met this urgent need while also a system that stategically uses `.yaml` configuration files to organizing file paths and run information as well as a `shapefile` as the source of information for each model node (e.g. depth, region name, etc).  I also introduced `SLURM arrays` in bash scripts to help facilitate batch processing of multiple runs.  I have tried to address the places where urgent need won over my senses of good coding practices but may have missed some spots.  Please contact me if you have any questions.  

If using or adapting this code for publications, presentations, or reports, then please cite this repository.

A special thanks to Ben Roberts for sharing information and his `ssmhist2netcdf`_ code for post-processing SalishSeaModel output.  Thanks as well to Su Kyong Yun (PNNL) for her help and guidance in developing this code.  

`Project Contributors`_ lists those who have contributed to this project and `Cookbook`_ shows "recipes" on how to use the files in this repository to cook up graphics, tables, and movies.  

Licenses
========
:License: Apache License, Version 2.0

All contents in this repository copyright 2022 by Rachael Mueller.  They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0.  Please see the LICENSE file for details of the license.   



.. _Project Contributors: https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst
.. _University of Washington: https://www.pugetsoundinstitute.org
.. _Cookbook: https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/creating_graphics_movies.md
.. _ssmhist2netcdf: https://github.com/bedaro/ssm-analysis/tree/main/ssmhist2cdf
