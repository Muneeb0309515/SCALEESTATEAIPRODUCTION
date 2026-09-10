import unittest
from datetime import datetime, timezone
from backend.app.motivation.engine import detect_motivation_signals
from backend.app.motivation.schemas import MotivationInput


class MotivationTests(unittest.TestCase):
    def test_detects_only_documented_threshold_signals(self):
        result = detect_motivation_signals(MotivationInput(estimated_equity=150001, estimated_market_value=300000, ownership_duration_years=10.1, days_on_market=181, source="provider", source_confidence="verified", detected_at=datetime.now(timezone.utc)))
        self.assertEqual([signal.signal_type for signal in result.signals], ["HIGH_EQUITY", "LONG_OWNERSHIP", "LONG_DOM"])
        self.assertEqual(result.motivation_score_state, "CONFIGURATION_REQUIRED")
    def test_does_not_infer_signal_from_unknown_input(self):
        result = detect_motivation_signals(MotivationInput(source="provider", source_confidence="verified", detected_at=datetime.now(timezone.utc)))
        self.assertEqual(result.signals, [])

if __name__ == "__main__": unittest.main()
