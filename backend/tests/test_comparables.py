import unittest
from datetime import date, timedelta
from backend.app.comparables.engine import analyze_comparables
from backend.app.comparables.schemas import ComparableCandidate, ComparableConfiguration


class ComparableTests(unittest.TestCase):
    def setUp(self):
        self.configuration = ComparableConfiguration(search_date=date(2026, 8, 28), max_distance_miles=3, max_sale_age_days=180, max_living_area_deviation=.2, outlier_mad_multiplier=3)
    def candidate(self, identifier, price, **changes):
        defaults = {"comparable_id": identifier, "sale_price": price, "distance_miles": 1, "sale_date": date(2026, 8, 1), "living_area_deviation": .05, "distance_score": 1, "recency_score": 1, "similarity_score": 1, "quality_score": 1}
        defaults.update(changes)
        return ComparableCandidate(**defaults)
    def test_excludes_mad_outlier_and_returns_weighted_arv(self):
        result = analyze_comparables([self.candidate("a", 200000), self.candidate("b", 210000), self.candidate("c", 205000), self.candidate("d", 600000)], self.configuration)
        review = next(item for item in result.reviews if item.comparable_id == "d")
        self.assertTrue(review.outlier)
        self.assertEqual(review.excluded_reason, "MAD outlier")
        self.assertEqual(result.weighted_arv, 205000)
    def test_override_requires_reason_and_creates_audit_handoff(self):
        result = analyze_comparables([self.candidate("a", 200000, selected_by_user=False, override_reason="Documented condition issue")], self.configuration)
        self.assertTrue(result.reviews[0].audit_event_required)
        self.assertEqual(result.reviews[0].excluded_reason, "User excluded comparable")

    def test_no_arv_is_returned_below_minimum_qualified_count(self):
        result = analyze_comparables([self.candidate("a", 200000), self.candidate("b", 210000)], self.configuration)
        self.assertEqual(result.arv_state, "INSUFFICIENT_DATA")
        self.assertIsNone(result.weighted_arv)

if __name__ == "__main__": unittest.main()
