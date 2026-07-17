#!/usr/bin/env python3

import unittest
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point
import xarray as xr
import numpy as np

# Software under test
sys.path.append(str(Path(__file__).parent.parent / 'py_scripts'))
from ssm_utils.depth import DepthReducer

class TestDepthReducer(unittest.TestCase):
    def setUp(self):
        # Set up mock grid of 4 nodes
        self.mock_gdf = gpd.GeoDataFrame({
            'depth': [0.05, 0.1, 0.15, 0.2],
            'geometry': gpd.GeoSeries([
                Point(1, 1), Point(1, 2), Point(2, 1), Point(2, 2)
            ])
        })
        # Six depth layers
        self.ssm_config = {'siglev_diff': [5, 10, 20, 30, 35]}

    def test_layer_sel_3d(self):
        dr = DepthReducer(ssm_config=self.ssm_config, gdf=self.mock_gdf)
        data = xr.DataArray([[[0,0,0,0],
                              [4,3,2,1],
                              [3,2,1,4],
                              [2,1,4,3],
                              [1,4,3,2],
                              [6,6,6,6]]],
                            dims=('day','siglay','node'))
        # All the trivial tests
        data_top = dr.select_depth(data, 'tp')
        self.assertEqual(('day','node'), data_top.dims)
        self.assertTrue((data_top == 0).all())

        data_bottom = dr.select_depth(data, 'bt')
        self.assertTrue((data_bottom == 6).all())

        data_mid = dr.select_depth(data, 'md')
        self.assertTrue((data_mid == 1).all())

        data_midavg = dr.select_depth(data, 'mA')
        self.assertTrue((data_midavg == 2.5).all())

        data_mean = dr.select_depth(data, 'wA')
        self.assertAlmostEqual(data_mean[0,0].item(), 2.66666667)

        data_min = dr.select_depth(data, 'wc')
        self.assertTrue((data_min == 0).all())

        # Select by depth
        data_120m = dr.select_depth(data, 'depth', depth=120)
        # The first and second node are too shallow
        self.assertTrue(np.isnan(data_120m[0,0]))
        self.assertTrue(np.isnan(data_120m[0,1]))
        # The third node should select the bottom layer
        self.assertEqual(data_120m[0,2], 6)
        # The fourth node should select the fifth layer
        self.assertEqual(data_120m[0,3], 2)

if __name__ == '__main__': unittest.main()
