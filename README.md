# Salish Sea Model Analysis at Puget Sound Institute (PSI)
This repository contains a collection of post-processing files designed to create tables, graphics, and movies from Salish Sea Model output. This work was funded by King County.

The most current version of the PSI code supports computing the Metabolic Index for three species across Puget Sound and the Straits for the published report, with code contributed by Ben Roberts and Stefano Mazzilli.

The repository also incorporates most of the code used to produce dissolved oxygen metrics and data for prior reports published by PSI. This includes the series of sensitivity analysis reports for the Northern Bays (including Bellingham), Whidbey, and Main Basin regions (lead contributor of code: Rachael Mueller), with details on the prior code used for those reports available [here](https://github.com/UW-PSI/SalishSeaModel-analysis/releases/tag/v1.1). Further updates and additional dissolved oxygen metrics were made by Ben Roberts and Stefano Mazzilli and applied in subsequent PSI reports. It is recommended to use this most recent version of all code (described further below), which is maintained going forward.

See the [project website](https://www.pugetsoundinstitute.org/nutrients/) on the PSI web pages for all reports using this code.

![SSM Node map](graphics/NodeMap_All_ECYcolors.png)

## General Organization

The directory [py_scripts](py_scripts/) contains all of the low-level processing code in the form of Python scripts that can be executed on the command line. The required Python environment is defined in [environment.yml](environment.yml). Most intensive computation is handled by the package [ssm_utils](py_scripts/ssm_utils/). [Unit tests](tests/) mostly apply to this package. Some extra one-off investigative, debugging, or plotting code is in the form of [Jupyter notebooks](notebooks/), although much of this is not used regularly in the workflow and/or requires changes to adapt it to your specific outputs and environment.

Python scripts generally read a YAML-formatted case file to know where various dependencies can be found, and the values of specific critical parameters. The scripts are usually best executed via shell scripts to assemble a full post-processing workflow; full examples of such workflows can be found in [examples](examples/), including [for our latest metabolic index study](examples/metabolic_index/).

Please contact Stefano (mazzilli@uw.edu) if you intend to use this code, wish to collaborate in some way, or wish to receive processed outputs or any additional components you may need. In particular, we are seeking collaboration with folks working on habitat assessment and water quality impacts on species of the Salish Sea, and welcome any collaboration that may be able to use or advance the aerobic habitat products in this repository and associated datasets.

## License and Copyright
All contents in this repository copyright (c) 2022-2026 by University of
Washington and created by Rachael D. Mueller/Ben Roberts (unless otherwise
specified) in collaboration with the [Project
Contributors](docs/CONTRIBUTORS.rst) at the [University of Washington's
Puget Sound Institute](https://www.pugetsoundinstitute.org). This work was
funded by King County.
