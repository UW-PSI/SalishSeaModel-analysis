# Created by Ben Roberts at the Puget Sound Institute with funding from King County

import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class FileFinder():
    case: str
    ssm_config: dict
    vtype: str='DOXG'
    mitype: str=None
    mispecies: str=None
    run_type: str=None
    check_exists: bool=True

    def __post_init__(self):
        if not self.processed_netcdf_dir.is_dir():
            if self.check_exists:
                raise FileNotFoundError(f'Directory {self.processed_netcdf_dir} not found')
            self._run_types = []
        else:
            self._run_types = os.listdir(self.processed_netcdf_dir) if self.run_type is None else [self.run_type]
        if self.check_exists and len(self._run_types) == 0:
            raise FileNotFoundError('No matching runs found to read from')

    @property
    def processed_netcdf_dir(self):
        """Base directory where intermediate netcdf files can be found"""
        return Path(self.ssm_config['paths']['processed_output']) / self.case / self.vtype

    @property
    def run_types(self):
        """lists all available run_types found"""
        return self._run_types

    def get_var_name(self, file_path: Path):
        """Principal variable name in an intermediate netcdf file"""
        parts = file_path.stem.split('_')
        assert parts[0] == 'daily', file_path.stem
        if self.vtype != 'mi':
            return f'{parts[2]}_daily_{parts[1]}_{parts[-1]}'
        else:
            return f'Mindex_daily_{parts[1]}_{parts[-1]}'

    def get_file(self, run_type: str, daily_type: str, depth_type='wc'):
        """Path to an intermediate netcdf file

        No validation is done that the file exists
        """
        if self.vtype != 'mi':
            f = self.processed_netcdf_dir / run_type / depth_type / f'daily_{daily_type}_{self.vtype}_{depth_type}.nc'
        else:
            f = self.processed_netcdf_dir / run_type / depth_type / f'daily_{daily_type}_MI_{self.mispecies}_{self.mitype}_{depth_type}.nc'
        if self.check_exists and not f.is_file():
            raise FileNotFoundError(f)
        return f

    @property
    def output_var_base(self):
        """Base of output file names"""
        if self.vtype != 'mi':
            return self.vtype
        else:
            return f'MI{self.mitype}_{self.mispecies}'
