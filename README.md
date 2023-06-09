***
# Salish Sea Model analysis at Puget Sound Institute 
***
This repository contains a collection of post-processing files designed to create tables, graphics, and movies from Salish Sea Model output.  The work was funded by King County and the coding platform was designed and developed by Rachael D. Mueller (unless otherwise specified) under the supervision of Stefano Mazzilli and Joel Baker.  This work was also in collaboration with Ben Roberts, Su Kyong Yun, and Marielle Larson.  See [contributors](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst) for a full overview of this collaboritive effort.  

The focus of this project was to better understand the how nitrogen in rivers and waste water treatment plants affects oxygen levels in the Salish Sea, as delineated by regions established by the Washington State Department of Ecology and shown below. 

<img src="https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/graphics/NodeMap_All_ECYcolors.png" width="400" />

My job was to develop the coding platform and analyses to address questions of how these different regions respond to changes in nutrient inputs from rivers and wastewater treatment plants.  I was asked to make the magic happen to produce requested information and to do so in a way that aligned with the project goals of enhancing transparency.  My accomplishments include: 
1. Reducing the turn-around time on post-processing model output from weeks to days.
2. Strategically developing code in order to produce a well-organized and efficient system while meeting an urgent need that was established prior to my being hired.
3. Identifying the mathematical equivalent of a series of logic statements that were used in a "rounding method" to quantify deviations in dissolved oxygen (used in a regulatory standard) and simplifying the calculation of [noncompliance](py_scripts/calc_noncompliance.py) with a mathematically equivalent, albeit more simple, approach.  
4. Developing information on marine conditions.  [Click here for some examples of graphics and links to code](/docs/graphic_examples.md). 
5. Creating a method to batch process runs and synthesize requested information via:
    1.  [spreadsheets](/docs/creating_graphics_movies.md#tables-), 
    2.  [graphics](docs/creating_graphics_movies.md#graphics-), and 
    3.  [movies](/docs/creating_graphics_movies.md#animations-)...or....
    4.  [all of the above](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/creating_graphics_movies.md).  

The system that I developed stategically uses a `.yaml` configuration files to organizing file paths and run information as well as using a `shapefile` as the source of information for each model node (e.g. depth, region name, etc).  I also introduced `SLURM arrays` in bash scripts to help facilitate batch processing of multiple runs.  This system relies on files that are version-controlled on two different repositories, both of which are only visible/accessible by project collaborators (at the time of this posting): 
1. https://github.com/UW-PSI/SalishSeaModel-grid
2. https://github.com/UW-PSI/SalishSeaModel-spreadsheets

These repositories ought to be cloned at the same directory level as this repository, using the repository names above (especially for the grid repository).  They were all tagged with `version-1` to benchmark completion of this project.  Results from this work have been incorporated into three reports (one each for the SOG/Bellingham, Whidbey, and Main regions) as well as workshop presentations that have knowledge-shared with around 400 participants.  

Please note: I have tried to address the places where urgent need won over my senses of better/preferred coding practices, but I probably missed some spots.  I also had plans to further streamline this process but had to leave this project "as is."  Please contact me if you see something wonky.  

A special thanks to Ben Roberts for sharing information and his [ssmhist2netcdf](https://github.com/bedaro/ssm-analysis/tree/main/ssmhist2cdf) code for post-processing SalishSeaModel output.  Thanks as well to Su Kyong Yun (PNNL) for her help and guidance in developing this code. [Project Contributors](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst) lists those who have contributed to this project.  

License and Copyright
========
:License: Please see the [LICENSE](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/LICENSE) file for details.

All contents in this repository copyright (c) 2022 by King County and created by Rachael D. Mueller (unless otherwise specified) in collaboration with the [Project Contributors](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/CONTRIBUTORS.rst) at the [University of Washington's Puget Sound Institute](https://www.pugetsoundinstitute.org).

An overview of most of the products created by these scripts can be found in [Table of Contents](https://github.com/RachaelDMueller/SalishSeaModel-analysis/blob/main/docs/creating_graphics_movies.md).
