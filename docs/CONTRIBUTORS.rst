.. _CONTRIBUTORS:

**********************************************
Contributors to this repository
**********************************************

This project was funded by King County.  The coding platform was designed and developed by Rachael D. Mueller under the supervision of `Stefano Mazzilli`_ and `Joel Baker`_ and in collaboration with `Tarang Khangaonkar`_ 
at the University of Washington's `Puget Sound Institute`_ and `PNNL`_. Stefano Mazzilli and Joel Baker defined the model setup and nutrient loading scenario specifications, with input from King County.  Su Kyong Yun and Tarang Khangaonkar provided the modeling expertise to implement the scenarios.  Most scenarios were run prior to the start of my work, although I was responsible for some (see filepaths for details).

More details on contributions to code development follow:

* Rachael Mueller <RachaelDMueller@gmail.com> (Was development lead for creating this SalishSeaModel post-processing system, the code, and the repository.  Rachael also setup and ran some of the model results evaluated here.)
* Sukyong Yun <sukyong.yun@pnnl.gov> (Provided Salish Sea Model output, an understanding of output file structure, and insights to post-processing methods.  She was an invaluable source of information on the Salish Sea Model version used for these graphics.  She also provided some output information for graphics and tables for the SOG/N.Bays regional analysis.)
* Ben Roberts <bedaro@uw.edu> (Provided code for converting Salish Sea Model output files to netcdf (see `ssmhist2netcdf`_.  He was also an invaluable source of knowledge on Salish Sea Model output format and inspired the method of plotting output using a shapefile.)
* Kevin Bogue <kbogue13@uw.edu> (Provided the shapefile after downloading Ecology's version and adding attributes in ArcGIS. The shapefile used in this work is version controlled in `SalishSeaModel-grid`_).
* Marielle Larson <marlars@uw.edu> (Guided graphic design and narration.  She also provided thoughtful input and feedback throughout. ). 

A special thanks to Doug Latornell in Susan Allen's lab at the University of British Columbia for generously sharing his knowledge on how to `create a good working environment`_ to support academic code development. 

.. _Stefano Mazzilli: https://www.pugetsoundinstitute.org/people/stefano-mazzilli/
.. _Joel Baker: https://www.pugetsoundinstitute.org/people/joel-baker-ph-d/
.. _Tarang Khangaonkar: https://www.pnnl.gov/people/tarang-khangaonkar
.. _Puget Sound Institute: https://www.pugetsoundinstitute.org
.. _PNNL: https://www.pnnl.gov
.. _create a good working environment: https://salishsea-meopar-docs.readthedocs.io/en/latest/work_env/index.html
.. _SalishSeaModel-grid: https://github.com/UW-PSI/
.. _ssmhist2netcdf: https://github.com/bedaro/ssm-analysis/tree/main/ssmhist2cdf
