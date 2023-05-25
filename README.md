***
# Salish Sea Model analysis at Puget Sound Institute 
***
This repository contains a collection of post-processing files designed to create tables, graphics, and movies from Salish Sea Model output.  The focus of this project was to better understand the how nitrogen in rivers and waste water treatment plants affects oxygen levels in the Salish Sea, as delineated by regions established by the Washington State Department of Ecology and shown below. 

<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/NodeMap_All_ECYcolors.png" width="400" />

My job was to develop the coding platform and analyses to address questions of how these different regions respond to changes in nutrient inputs from rivers and wastewater treatment plants.  My accomplishments include: 
1. Reducing the turn-around time on post-processing model output from weeks to days.
2. Developing information on marine conditions.  [Click here for some examples of graphics and links to code](/docs/graphic_examples.md). 
3. Being strategic in code development in order to produce a well-organized and efficient system while meeting an urgent need that was established prior to my being hired.
4. Creating a method to batch process runs and synthesize analyses in spreadsheets, tables, and graphics.  [Click here for links to the code to develop these products](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/creating_graphics_movies.md).  

The system that I developed stategically uses a `.yaml` configuration files to organizing file paths and run information as well as using a `shapefile` as the source of information for each model node (e.g. depth, region name, etc).  I also introduced `SLURM arrays` in bash scripts to help facilitate batch processing of multiple runs.  Results from this work have been incorporated into three reports (one each for the SOG/Bellingham, Whidbey, and Main regions) as well as workshop presentations.  

Please note: I have tried to address the places where urgent need won over my senses of better/preferred coding practices, but I probably missed some spots.  I also had plans to further streamline this process but had to leave this project "as is."  Please contact me if you see something wonky.  

A special thanks to Ben Roberts for sharing information and his [ssmhist2netcdf](https://github.com/bedaro/ssm-analysis/tree/main/ssmhist2cdf) code for post-processing SalishSeaModel output.  Thanks as well to Su Kyong Yun (PNNL) for her help and guidance in developing this code. [Project Contributors](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst) lists those who have contributed to this project.  

Licenses
========
:License: Apache License, Version 2.0

All contents in this repository copyright 2022 by Rachael Mueller and [University of Washington](https://www.pugetsoundinstitute.org).  They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0.  Please see the [LICENSE](/LICENSE) file for details of the license and reference this repository if using or adapting this work.

