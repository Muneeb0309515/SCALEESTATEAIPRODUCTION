import unittest
from backend.app.matching.engine import match_buyer
from backend.app.matching.schemas import BuyerCriteria, DealCandidate, MatchConfiguration


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.config = MatchConfiguration(high_confidence_threshold=.8, medium_confidence_threshold=.5)
        self.deal = DealCandidate(market="Dallas", zip_code="75201", property_type="single_family", purchase_price=200000, arv=300000, wholesale_spread=40000, requires_financing=False, buyer_activity_score=1)

    def test_retains_reasons_and_failures_with_deterministic_score(self):
        buyer = BuyerCriteria(buyer_id="buyer-a", markets={"Dallas"}, zip_codes={"75201"}, property_types={"single_family"}, price_min=100000, price_max=250000, arv_min=250000, arv_max=350000, minimum_spread=40000, cash_only=True)
        result = match_buyer(self.deal, buyer, self.config)
        self.assertEqual(result.match_score, 1)
        self.assertEqual(result.confidence, "high")
        self.assertIn("Buyer operates in Dallas", result.match_reasons)

    def test_outside_range_is_a_visible_failed_criterion(self):
        buyer = BuyerCriteria(buyer_id="buyer-b", markets={"Dallas"}, zip_codes={"75201"}, property_types={"single_family"}, price_min=100000, price_max=190000, arv_min=250000, arv_max=350000, minimum_spread=40000, cash_only=True)
        result = match_buyer(self.deal, buyer, self.config)
        self.assertIn("Purchase price is unavailable or outside range", result.failed_criteria)
        self.assertEqual(result.factor_scores["price"], 0)

if __name__ == "__main__": unittest.main()
