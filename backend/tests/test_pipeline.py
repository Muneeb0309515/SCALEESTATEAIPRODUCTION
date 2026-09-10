import unittest
from datetime import date
from backend.app.workflows.pipeline import DealStage, TransitionInput, validate_transition


class PipelineTests(unittest.TestCase):
    def test_rejects_stage_skipping(self):
        result = validate_transition(TransitionInput(current_stage=DealStage.NEW, new_stage=DealStage.RESEARCHING))
        self.assertFalse(result.allowed)
        self.assertEqual(result.status_code, 409)

    def test_under_contract_requires_snapshot_price_and_date(self):
        result = validate_transition(TransitionInput(current_stage=DealStage.CONTRACT_PENDING, new_stage=DealStage.UNDER_CONTRACT))
        self.assertFalse(result.allowed)
        self.assertEqual(result.status_code, 422)

    def test_under_contract_emits_all_critical_handoffs(self):
        result = validate_transition(TransitionInput(current_stage=DealStage.CONTRACT_PENDING, new_stage=DealStage.UNDER_CONTRACT, contract_price=210000, closing_date=date(2026, 10, 15), analysis_snapshot={"mao": 220000, "arv": 300000}))
        self.assertTrue(result.allowed)
        self.assertIn("create_immutable_analysis_snapshot", result.required_actions)
        self.assertIn("queue_deterministic_buyer_matching", result.required_actions)

if __name__ == "__main__": unittest.main()
