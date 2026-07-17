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
from ssm_utils.vol_area_stats import VolAreaStats

class TestVolAreaStats(unittest.TestCase):
    def setUp(self):
        # Set up mock grid of 4 nodes
        self.mock_gdf = gpd.GeoDataFrame({
            'included_i': [True, True, True, False],
            'Regions': ['A', 'A', 'B', 'B'],
            'Area_m2': [500, 1000, 500, 500],
            'volume': [5000, 8000, 6000, 6000],
            'geometry': gpd.GeoSeries([
                Point(1, 1), Point(1, 2), Point(2, 1), Point(2, 2)
            ])
        })
        # Four depth layers
        self.ssm_config = {'siglev_diff': [10, 20, 30, 40]}

    def test_init(self):
        obj = VolAreaStats(self.ssm_config, self.mock_gdf, {'day': 3, 'siglay': 4, 'node': 4})
        self.assertAlmostEqual(obj.volume[0,1].item(), 800)
        self.assertAlmostEqual(obj.area[2].item(), 0.0005) # it's in km2

        self.assertEqual(obj.ndays, 3)
        self.assertEqual(obj.nlevels, 4)
        self.assertEqual(obj.nnodes, 4)

    def test_brief_exposure(self):
        obj = VolAreaStats(self.ssm_config, self.mock_gdf, {'day': 6, 'siglay': 4, 'node': 4})

        data = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        # Two days of exposure in cell 2, layer 2. 1600 km^3 volume
        data[1:3,1,1] = True
        vol_days = obj.apply(data)

        self.assertEqual(vol_days[1], 3200)

    def test_vol_by_region(self):
        obj = VolAreaStats(self.ssm_config, self.mock_gdf, {'day': 6, 'siglay': 4, 'node': 4})
        self.assertEqual(obj.ndays, 6)

        data = xr.DataArray(np.zeros((6,4,4), dtype=bool), dims=['day','siglay','node'])
        # create exposures for both nodes in region A
        data[1:4,0,0] = True
        data[2:5,1,1] = True
        vol_days = obj.apply(data)

        days, vol_days_region, pct_vol_days, daily_vols = obj.get_vol_stats_by_region('A')

        self.assertEqual(days, 4)
        self.assertEqual(vol_days_region, 500*3+1600*3)
        self.assertEqual(daily_vols[1], 500)
        self.assertEqual(daily_vols[2], 2100)
        self.assertEqual(daily_vols[4], 1600)

if __name__ == '__main__': unittest.main()
