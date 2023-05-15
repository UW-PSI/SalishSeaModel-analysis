***
# Salish Sea Model analysis at Puget Sound Institute 
***
This repository contains a collection of post-processing files designed to create tables, graphics, and movies from Salish Sea Model output.  The project focused on understanding nutrient loading impacts in regions deliniated by the Washington State Department of Ecology and shown below. 

Here is a link to [some examples of graphics](/docs/graphic_examples.md).

![ECY compliance regions](/graphics/NodeMap_All_ECYcolors.png "ECY compliance regions")

My job was to develop the coding platform and analyses to develop this knowledge.  My goal was to be strategic in code development in ordder to produce a well-organized and efficient system; but I was hired onto this project when there was already an urgent need to produce results.  I did my best to meet this urgent need while also creating a sustaining system by stategically developing `.yaml` configuration files to organizing file paths and run information as well as using a `shapefile` as the source of information for each model node (e.g. depth, region name, etc).  I also introduced `SLURM arrays` in bash scripts to help facilitate batch processing of multiple runs.  

I have tried to address the places where urgent need won over my senses of better/preferred coding practices, but I probably missed some spots.  Please contact me if you have any questions.  

A special thanks to Ben Roberts for sharing information and his [ssmhist2netcdf](https://github.com/bedaro/ssm-analysis/tree/main/ssmhist2cdf) code for post-processing SalishSeaModel output.  Thanks as well to Su Kyong Yun (PNNL) for her help and guidance in developing this code.  

[Project Contributors](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst) lists those who have contributed to this project and [Cookbook](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/creating_graphics_movies.md) shows "recipes" on how to use the files in this repository to cook up graphics, tables, and movies.  

Licenses
========
:License: Apache License, Version 2.0

All contents in this repository copyright 2022 by Rachael Mueller and [University of Washington](https://www.pugetsoundinstitute.org).  They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0.  Please see the LICENSE file for details of the license and reference this repository if using or adapting this code for publications, presentations, or reports.

