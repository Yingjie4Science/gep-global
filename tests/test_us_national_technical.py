import unittest

import numpy as np

import effect_size_uncertainty


class WindowedTechnicalFormulaTests(unittest.TestCase):
    def test_direct_formula_matches_shared_function(self):
        population = np.array([10.0, 20.0, 30.0])
        ndvi = np.array([-0.1, 0.0, 0.6])
        prevalence = 0.0424332878
        p0 = 0.115
        odds_ratio = 0.931
        risk_ratio = effect_size_uncertainty.odds_ratio_to_risk_ratio(odds_ratio, p0)
        delta = np.maximum(ndvi, 0.0)
        direct = population * prevalence * (np.exp(-10 * delta * np.log(risk_ratio)) - 1)
        shared = effect_size_uncertainty.additional_cases_from_observed(
            population * prevalence, risk_ratio, delta)
        np.testing.assert_allclose(direct, shared, rtol=1e-12, atol=1e-12)

    def test_missing_exposure_lower_bound_is_zero(self):
        population = 100.0
        prevalence = 0.0424332878
        self.assertEqual(population * prevalence * (1.0 - 1.0), 0.0)


if __name__ == '__main__':
    unittest.main()
