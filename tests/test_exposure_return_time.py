#!/usr/bin/env python3

import unittest
import sys
from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import xarray as xr
import numpy as np

# Software under test
sys.path.append(str(Path(__file__).parent.parent / 'py_scripts'))
from ssm_utils.exposure_return import ExposureReturn

class TestExposureReturnTime(unittest.TestCase):
    def setUp(self):
        # Set up mock grid of 4 nodes. Node indices are numbered starting from 1
        self.mock_gdf = gpd.GeoDataFrame({
            'included_i': [True, True, True, False],
            'Regions': ['A', 'A', 'B', 'B'],
            'Area_m2': [500, 1000, 500, 500],
            'volume': [5000, 8000, 6000, 6000],
            'geometry': gpd.GeoSeries([
                Point(1, 1), Point(1, 2), Point(2, 1), Point(2, 2)
            ]),
            'depth': [10, 8, 12, 12]
        }, index=pd.RangeIndex(1, 5))
        # Four depth layers
        self.ssm_config = {'siglev_diff': [10, 20, 30, 40]}

    def test_no_exposure(self):
        obj = ExposureReturn(self.ssm_config, self.mock_gdf, {'day': 6, 'siglay': 4, 'node': 4})

        data_min = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        data_max = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        obj.apply(data_min, data_max)
        # There should be no exposure OR recovery in this trivial case
        self.assertTrue(np.isnan(obj.exposure).all())
        self.assertTrue(np.isnan(obj.return_time).all())

    def test_brief_exposure(self):
        obj = ExposureReturn(self.ssm_config, self.mock_gdf, {'day': 6, 'siglay': 4, 'node': 4})

        data_min = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        # two days of exposure in one cell followed by three days of recovery
        data_min[1:3,1,1] = True
        data_max = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        obj.apply(data_min, data_max)
        # We check the cell itself, and ensure no other cells have non-NaN values by taking the sum
        self.assertEqual(obj.exposure[1,1,1].item(), 2)
        self.assertEqual(obj.exposure[:,1,1].sum().item(), 2)
        self.assertEqual(obj.return_time[3,1,1].item(), 3)
        self.assertEqual(obj.return_time[:,1,1].sum().item(), 3)
        # data_max was always False so there is no net exposure, and we count this as a partial recovery
        self.assertEqual(obj.partial_return[1,1,1].item(), 2)
        self.assertEqual(obj.partial_return[:,1,1].sum().item(), 2)
        self.assertTrue(np.isnan(obj.net_exposure).all())

        # Now test _fill_by_day
        by_day = obj.get_exposure_by_day()
        self.assertEqual(by_day[1,1,1].item(), 2)
        self.assertEqual(by_day[2,1,1].item(), 2)
        self.assertTrue(np.isnan(by_day[3,1,1]))
        self.assertTrue(np.isnan(by_day[4,1,1]))
        self.assertTrue(np.isnan(by_day[5,1,1]))

        # Now test get_exposure_by_node()
        by_node = obj.get_exposure_by_node()
        self.assertEqual(by_node.loc[2, 'exp_max'], 2)

    def test_start_end_in_exposure(self):
        obj = ExposureReturn(self.ssm_config, self.mock_gdf, {'day': 6, 'siglay': 4, 'node': 4})

        data_min = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        # two days of initial exposure in one cell followed by one day of recovery, then exposure through end
        data_min[[0,1,3,4,5],1,1] = True
        data_max = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        # This time data_max matches data_min except for day 2, so there's one day of partial recovery
        data_max[[0,3,4,5],1,1] = True
        obj.apply(data_min, data_max)
        self.assertEqual(obj.exposure[0,1,1].item(), 2)
        self.assertEqual(obj.exposure[3,1,1].item(), 3)
        self.assertEqual(obj.exposure[:,1,1].sum().item(), 5)
        self.assertEqual(obj.return_time[2,1,1].item(), 1)
        self.assertEqual(obj.return_time[:,1,1].sum().item(), 1)

        self.assertEqual(obj.partial_return[1,1,1].item(), 1)
        self.assertEqual(obj.partial_return[:,1,1].sum().item(), 1)

        self.assertEqual(obj.net_exposure[0,1,1].item(), 1)
        self.assertEqual(obj.net_exposure[:,1,1].sum().item(), 4)

if __name__ == '__main__': unittest.main()
