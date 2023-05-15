***
# Salish Sea Model analysis at Puget Sound Institute 
***
This repository contains a collection of post-processing files designed to create tables, graphics, and movies from Salish Sea Model output.  The project focused on understanding nutrient loading impacts in regions deliniated by the Washington State Department of Ecology and shown below. 

![ECY compliance regions](/graphics/NodeMap_All_ECYcolors.png "ECY compliance regions")

My job was to develop the coding platform and analyses to address questions of how these different regions respond to changes in nutrient inputs from rivers and wastewater treatment plants.  I was also asked to develop information on marine conditions.  Here is a link to [some examples of graphics](/docs/graphic_examples.md) showing marine conditions and regional characterics.  

My goal in this work was to be strategic in code development in ordder to produce a well-organized and efficient system; but I was hired onto this project when there was already an urgent need to produce results and no system or code in place to do so.  I did my best to meet the urgent need while also being strategic in my code development.  

The system that I developed stategically uses a `.yaml` configuration files to organizing file paths and run information as well as using a `shapefile` as the source of information for each model node (e.g. depth, region name, etc).  I also introduced `SLURM arrays` in bash scripts to help facilitate batch processing of multiple runs.  Results from this work have been incorporated into three reports (one each for the SOG/Bellingham, Whidbey, and Main regions) as well as workshop presentations.  

Please note: I have tried to address the places where urgent need won over my senses of better/preferred coding practices, but I probably missed some spots.  Please contact me if you have any questions.  

A special thanks to Ben Roberts for sharing information and his [ssmhist2netcdf](https://github.com/bedaro/ssm-analysis/tree/main/ssmhist2cdf) code for post-processing SalishSeaModel output.  Thanks as well to Su Kyong Yun (PNNL) for her help and guidance in developing this code.  

[Project Contributors](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst) lists those who have contributed to this project and [Cookbook](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/creating_graphics_movies.md) shows "recipes" on how to use the files in this repository to cook up graphics, tables, and movies.  

Licenses
========
:License: Apache License, Version 2.0

All contents in this repository copyright 2022 by Rachael Mueller and [University of Washington](https://www.pugetsoundinstitute.org).  They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0.  Please see the [LICENSE](/LICENSE) file for details of the license and reference this repository if using or adapting this code for publications, presentations, or reports.

