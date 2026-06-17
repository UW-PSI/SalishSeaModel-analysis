#!/usr/bin/env python3

import unittest
import sys

import numpy as np

# software under test
sys.path.append('../py_scripts')
from calc_mi import calc_mi

class TestCalcMi(unittest.TestCase):
    def setUp(self):
        # Model coefficients from fitted regression (Chinook Salmon specific)
        self.betas = np.array([1.58422927, -0.04328307, 0.17567401, -0.32428962])  # [intercept, size_effect, temp_effect, metabolic_mode]

        # Variance-covariance matrix of parameter estimates (captures parameter uncertainty)
        self.var_covar = np.array([
            [0.173846857, 1.326809e-02, -0.073963952, 6.287643e-03],  # Variances and covariances for intercept
            [0.013268092, 8.014129e-03, -0.004246992, 1.119302e-05],  # Variances and covariances for size effect
            [-0.073963952, -4.246992e-03, 0.035758738, -2.752385e-03],  # Variances and covariances for temperature effect
            [0.006287643, 1.119302e-05, -0.002752385, 2.331340e-02]   # Variances and covariances for metabolic mode
])
    def test_chinook_salmon(self):
        # Test code conditions inputs- Chinook Salmon
        w = 5  # Body weight in grams (reference size)
        temperature = 15  # Temperature in Celsius (reference temperature)
        method = "routine"  # Metabolic state: routine (active) vs SMR (resting)

        # Test Case 1 - Baseline Routine Metabolism (Should = 1.0)
        # Set pO2 to critical value where MI = 1 (pO2 = V and method = "routine"
        pO2 = np.exp(self.betas[0])  # Use exp of intercept coefficient to set critical oxygen level
        result = calc_mi(pO2, w, temperature, self.betas, self.var_covar, method="routine", confidence_level=0.95)  # Calculate MI with uncertainty
        self.assertAlmostEqual(1, result['mi'])
        self.assertAlmostEqual(0.441664, result['lower_bound'])
        self.assertAlmostEqual(2.2641648, result['upper_bound'])

        # Test Case 2 - Standard Metabolic Rate Comparison (Should > 1.0)
        # Same conditions but using SMR instead of routine metabolism
        result = calc_mi(pO2, w, temperature, self.betas, self.var_covar, method="smr", confidence_level=0.95)  # SMR has lower metabolic demands
        self.assertLess(1, result['mi'])
        self.assertAlmostEqual(1.3830478, result['mi'])
        self.assertAlmostEqual(0.563655, result['lower_bound'])
        self.assertAlmostEqual(3.3936032, result['upper_bound'])

        # Test Case 3 - Temperature Effect (Increasing (higher) Temperature should decrease MI)
        temperature = 20  # Increase temperature by 5°C from reference
        result = calc_mi(pO2, w, temperature, self.betas, self.var_covar, method="routine", confidence_level=0.95)  # Higher temperature increases metabolic demand
        self.assertGreater(1, result['mi'])

        # Test Case 4 - Body Size Effect (Larger organisms should have lower MI)
        w = 4000  # Increase body weight to 4kg (800x larger than reference)
        temperature = 15  # Reset temperature to reference value
        result = calc_mi(pO2, w, temperature, self.betas, self.var_covar, method="routine", confidence_level=0.95)  # Larger fish have higher mass-specific metabolic demands
        self.assertGreater(1, result['mi'])

    def test_arrays(self):
        # Test with arrays (this is where vectorization provides benefit)
        pO2_array = np.array([21.0, 15.0, 10.0])  # Multiple oxygen levels
        w_array = np.array([5, 100, 1000])        # Multiple body weights  
        temp_array = np.array([15, 18, 22])       # Multiple temperatures

        results_vectored = calc_mi(pO2_array, w_array, temp_array, self.betas, self.var_covar, 'routine')
        # Repeat each as a scalar calculation
        for i,(po2,w,temp) in enumerate(zip(pO2_array,w_array,temp_array)):
            r = calc_mi(po2, w, temp, self.betas, self.var_covar, 'routine')
            self.assertEqual(r['mi'], results_vectored['mi'][i])
            self.assertEqual(r['lower_bound'], results_vectored['lower_bound'][i])
            self.assertEqual(r['upper_bound'], results_vectored['upper_bound'][i])

if __name__ == '__main__': unittest.main()
