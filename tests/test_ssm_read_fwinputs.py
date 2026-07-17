#!/usr/bin/env python

import unittest
import sys
from io import StringIO
import pandas as pd
# software under test
sys.path.insert(0, sys.path[0] + '/../py_scripts')
import ssm_read_fwinputs

class TestSsmReadFwinputs(unittest.TestCase):
    def test_check_match(self):
        df1 = pd.DataFrame({'value': [1, 2, 3, 5]})
        df2 = pd.DataFrame({'value': [1, 2, 3, 5]})
        df3 = pd.DataFrame({'value': [1, 2, 3, 5], 'value2': [0, 0, 0, 0]})
        df4 = pd.DataFrame({'value': [1, 2, 3, 4]})
        df5 = pd.DataFrame({'value': [1, 2, 3, 5, 7]})
        self.assertEqual(ssm_read_fwinputs.dfs_match(df1, df2), True)
        self.assertEqual(ssm_read_fwinputs.dfs_match(df1, df3), True)
        self.assertEqual(ssm_read_fwinputs.dfs_match(df1, df4), ['value',])
        self.assertEqual(ssm_read_fwinputs.dfs_match(df1, df5), True)

    def test_read_dat_file(self):
        basic_riv = """infl pttype
4
26! comment1
87 ! comment2
94!comment3!comment
99
1 0.05 0.05 0.1 0.1 0.1 0.1
2 0.1 0.2 0.3 0.4 0.5 0.6
3 0.01 0.02 0.03 0.04 0.05 0.06
4 0.02 0.04 0.06 0.08 0.10 0.12
2
48
101 102 103 104
201 202 203 204
301 302 303 304
120
111 112 113 114
211 212 213 214
311 312 313 314"""

        dfs, inflow_type, point_st_type = ssm_read_fwinputs.read_dat_file(
                StringIO(basic_riv), pd.Timestamp('2000.01.01'),
                num_statevars=3)

        self.assertEqual(inflow_type, 'infl')
        self.assertEqual(point_st_type, 'pttype')

        self.assertEqual(len(dfs['nodes']), 4)
        self.assertEqual(dfs['nodes']['Node'].iloc[0], 26)
        self.assertEqual(dfs['nodes']['Node'].iloc[1], 87)
        self.assertEqual(dfs['nodes']['Node'].iloc[2], 94)
        self.assertEqual(len(dfs['data']), 8) # 4 nodes by 2 times

if __name__ == '__main__':
    unittest.main()
