#!/usr/bin/env python3

import unittest
import sys
from pathlib import Path

import numpy as np

# Software under test
sys.path.append(str(Path(__file__).parent.parent / 'py_scripts'))
import ssm_utils

class TestSsmUtils(unittest.TestCase):
    def setUp(self):
        # Data was randomly generated using
        # np.random.randint(0,10,size=(5,4,4,4))
        self.hourly_test_data = np.array(
                  [[[[2, 8, 8, 6],
                     [7, 1, 9, 9],
                     [4, 1, 0, 8],
                     [6, 9, 1, 7]],

                    [[6, 8, 6, 9],
                     [8, 8, 4, 5],
                     [5, 0, 2, 3],
                     [4, 3, 2, 9]],

                    [[0, 8, 4, 0],
                     [4, 8, 2, 4],
                     [3, 2, 9, 9],
                     [9, 9, 7, 5]],

                    [[3, 8, 2, 4],
                     [1, 0, 6, 8],
                     [6, 9, 8, 3],
                     [8, 9, 5, 5]]],


                   [[[5, 5, 1, 1],
                     [1, 1, 0, 6],
                     [6, 0, 9, 9],
                     [3, 6, 8, 5]],

                    [[3, 4, 7, 2],
                     [0, 6, 6, 7],
                     [9, 8, 0, 4],
                     [0, 1, 6, 7]],

                    [[4, 0, 6, 0],
                     [2, 7, 3, 9],
                     [3, 0, 6, 9],
                     [1, 7, 4, 7]],

                    [[6, 9, 5, 5],
                     [0, 6, 0, 4],
                     [9, 1, 6, 6],
                     [4, 9, 0, 8]]],


                   [[[7, 2, 7, 2],
                     [4, 1, 9, 8],
                     [9, 6, 0, 7],
                     [7, 3, 1, 7]],

                    [[5, 2, 4, 5],
                     [9, 7, 6, 7],
                     [2, 4, 3, 4],
                     [7, 8, 9, 4]],

                    [[3, 0, 2, 0],
                     [9, 9, 7, 7],
                     [7, 4, 6, 3],
                     [1, 1, 3, 8]],

                    [[4, 1, 7, 9],
                     [5, 1, 9, 3],
                     [3, 5, 3, 1],
                     [5, 9, 1, 7]]],


                   [[[0, 5, 3, 7],
                     [2, 5, 7, 3],
                     [5, 7, 0, 0],
                     [6, 3, 9, 3]],

                    [[7, 3, 2, 0],
                     [5, 1, 1, 0],
                     [1, 3, 0, 5],
                     [3, 2, 0, 5]],

                    [[6, 7, 2, 7],
                     [7, 9, 0, 3],
                     [6, 3, 5, 8],
                     [8, 1, 9, 5]],

                    [[2, 6, 7, 9],
                     [2, 4, 5, 5],
                     [4, 0, 6, 5],
                     [6, 5, 8, 9]]],


                   [[[1, 0, 0, 8],
                     [3, 9, 9, 5],
                     [7, 7, 5, 7],
                     [2, 0, 0, 9]],

                    [[1, 2, 3, 2],
                     [0, 1, 9, 0],
                     [9, 6, 9, 6],
                     [5, 4, 8, 7]],

                    [[5, 5, 6, 5],
                     [2, 2, 3, 4],
                     [5, 1, 5, 8],
                     [2, 9, 2, 1]],

                    [[9, 5, 7, 6],
                     [8, 1, 6, 3],
                     [6, 8, 7, 7],
                     [3, 4, 8, 7]]]])


    def test_calc_fvcom_stat_simple(self):
        red = ssm_utils.calc_fvcom_stat(self.hourly_test_data, 'mean', axis=1)
        self.assertEqual((5,4,4), red.shape)
        self.assertEqual(2.75, red[0,0,0])
        self.assertEqual(5, red[1,1,1])

        red = ssm_utils.calc_fvcom_stat(self.hourly_test_data, 'min', axis=1)
        self.assertEqual(0, red[0,0,0])
        self.assertEqual(4, red[1,2,3])

    def test_calc_fvcom_stat_context(self):
        data2 = np.random.randint(0, 10, size=self.hourly_test_data.shape)
        red, red2 = ssm_utils.calc_fvcom_stat(self.hourly_test_data, 'min', axis=1, context_from=[data2])
        self.assertEqual(0, red[0,0,0])
        self.assertEqual(4, red[1,2,3])

        self.assertEqual((5,4,4), red2.shape)
        # hourly_test_data.argmin(axis=1)[0,1,3] == 2
        self.assertEqual(data2[0,2,1,3], red2[0,1,3])
        # argmin[0,2,1] == 1
        self.assertEqual(data2[0,1,2,1], red2[0,2,1])
        # argmin[2,0,1] == 2
        self.assertEqual(data2[2,2,0,1], red2[2,0,1])
        # argmin[3,2,1] == 3
        self.assertEqual(data2[3,3,2,1], red2[3,2,1])

if __name__ == '__main__': unittest.main()
