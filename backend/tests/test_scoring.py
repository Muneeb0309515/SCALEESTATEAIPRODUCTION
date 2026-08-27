import unittest
from backend.app.scoring.engine import calculate_final_classification, calculate_weighted_score
from backend.app.scoring.schemas import ClassificationConfiguration, WeightedScoreConfiguration, WeightedScoreInput


class ScoringTests(unittest.TestCase):
    def test_calculates_only_from_explicit_configuration(self):
        score = calculate_weighted_score(WeightedScoreInput(factors={"equity": .8, "motivation": .6}), WeightedScoreConfiguration(weights={"equity": .5, "motivation": .5}, favorable_threshold=.7, moderate_threshold=.4))
        self.assertEqual(score, .7)
    def test_rejects_mismatched_factor_configuration(self):
        with self.assertRaises(ValueError):
            calculate_weighted_score(WeightedScoreInput(factors={"equity": .8}), WeightedScoreConfiguration(weights={"equity": .5, "motivation": .5}, favorable_threshold=.7, moderate_threshold=.4))
    def test_returns_unknown_without_configured_classification(self):
        result = calculate_final_classification(.8, .1, None)
        self.assertEqual(result.state, "CONFIGURATION_REQUIRED")
        self.assertEqual(result.label, "UNKNOWN")
    def test_classification_follows_provided_thresholds(self):
        config = ClassificationConfiguration(strong_deal_score_minimum=.75, moderate_deal_score_minimum=.5, acceptable_risk_maximum=.3, caution_risk_maximum=.6)
        self.assertEqual(calculate_final_classification(.8, .2, config).label, "STRONG_DEAL")
        self.assertEqual(calculate_final_classification(.8, .8, config).label, "HIGH_RISK")

if __name__ == "__main__": unittest.main()
