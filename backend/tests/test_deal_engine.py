import unittest
from backend.app.deal_engine.engine import calculate_analysis
from backend.app.deal_engine.schemas import AnalysisAssumptions, AnalysisInput, DataClassification, ProvenancedNumber, ResultState

def calculated(value): return ProvenancedNumber(value=value, classification=DataClassification.CALCULATED_DATA, source="deterministic_engine")
def user_input(value): return ProvenancedNumber(value=value, classification=DataClassification.USER_INPUT, source="user")

class DealEngineTests(unittest.TestCase):
    def test_mao_uses_the_authoritative_formula(self):
        result = calculate_analysis(AnalysisInput(arv=calculated(300000), repair_cost=user_input(15000), assumptions=AnalysisAssumptions(mao_percentage=user_input(.70), desired_profit=user_input(60000))))
        self.assertEqual(result.mao.state, ResultState.CALCULATED)
        self.assertEqual(result.mao.value, 135000)
    def test_equity_is_unknown_without_debt(self):
        result = calculate_analysis(AnalysisInput(estimated_market_value=calculated(300000)))
        self.assertEqual(result.equity.state, ResultState.UNKNOWN)
        self.assertIsNone(result.equity.value)
    def test_margin_is_unknown_with_zero_purchase_price(self):
        result = calculate_analysis(AnalysisInput(expected_assignment_price=user_input(100000), purchase_contract_price=user_input(0)))
        self.assertEqual(result.wholesale_margin.state, ResultState.UNKNOWN)
    def test_ai_estimate_cannot_be_used_as_arv(self):
        result = calculate_analysis(AnalysisInput(arv=ProvenancedNumber(value=310000, classification=DataClassification.AI_ESTIMATE)))
        self.assertEqual(result.arv.state, ResultState.INSUFFICIENT_DATA)

if __name__ == "__main__": unittest.main()
