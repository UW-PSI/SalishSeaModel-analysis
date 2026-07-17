# Created by Ben Roberts at the Puget Sound Institute with funding from King County

import os
import pwd
import logging

from pathlib import Path
import yaml

def read_case(casename_or_file):
    """Load YAML file containing path definitions etc
    
    Gets case information given either a case name or a YAML file path.
    
    These files typically live in etc are created by the notebook SSM_config_*.ipynb in etc.
    Any modifications to the YAML files are lost if the notebook is re-run.

    Returns the read data and the case name, which may be different from the
    argument given if the argument was a path to the file.
    """
    logger = logging.getLogger('ssm_utils.read_case')
    pth = Path(casename_or_file)
    if not (pth.is_file() and pth.suffix == '.yaml'):
        # Treat it as the case name and look for the YAML file in
        # the global config directory
        case = casename_or_file
        pth = Path(__file__).parent.parent / 'etc' / f'SSM_config_{case}.yaml'
    else:
        # Determine case once we've read the file
        case = None
    with open(pth, 'r') as file:
        ssm = yaml.safe_load(file)
    if case is None:
        # We can guess case name by looking at the keys of
        # ssm['run_information']['run_description_short'] and
        # ssm['paths']['model_output']. If it doesn't work throw
        # an error
        model_output_keys = ssm['paths']['model_output'].keys()
        assert len(model_output_keys) == 1
        run_desc_keys = ssm['run_information']['run_description_short'].keys()
        assert len(run_desc_keys) == 1
        case = list(model_output_keys)[0]
        assert case == list(run_desc_keys)[0]
        logger.info(f'Inferring case name to be {case}')
    return apply_defaults(ssm), case

def apply_defaults(ssm_config):
    ssm_config.setdefault('author', pwd.getpwuid(os.getuid()).pw_gecos.split(',')[0])
    return ssm_config
