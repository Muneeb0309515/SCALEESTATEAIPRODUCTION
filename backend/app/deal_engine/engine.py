"""Formulae constrained to DETERMINISTIC_DEAL_ANALYSIS_ENGINE.md."""

from .schemas import AnalysisInput, AnalysisResult, DataClassification, MetricResult, ResultState


def _unknown(reason: str, state: ResultState = ResultState.UNKNOWN) -> MetricResult:
    return MetricResult(state=state, reason=reason)


def _number(number, name: str):
    if number is None or number.value is None or number.classification == DataClassification.UNKNOWN:
        return None, f"{name} is unavailable"
    return number.value, None


def _calculated(value: float, formula: str, **inputs: float) -> MetricResult:
    return MetricResult(state=ResultState.CALCULATED, value=round(value, 2), formula=formula, inputs=inputs)


def calculate_analysis(data: AnalysisInput) -> AnalysisResult:
    arv, arv_error = _number(data.arv, "ARV")
    if data.arv and data.arv.classification == DataClassification.AI_ESTIMATE:
        arv, arv_error = None, "ARV cannot be an AI_ESTIMATE"
    market, market_error = _number(data.estimated_market_value, "Estimated market value")
    debt, debt_error = _number(data.outstanding_debt, "Outstanding debt")
    repair, repair_error = _number(data.repair_cost, "Repair cost")
    purchase, purchase_error = _number(data.purchase_contract_price, "Purchase contract price")
    assignment, assignment_error = _number(data.expected_assignment_price, "Expected assignment price")
    asking, asking_error = _number(data.asking_price, "Asking price")
    sale, sale_error = _number(data.expected_sale_price, "Expected sale price")
    profit, profit_error = _number(data.net_profit, "Net profit")

    equity = _calculated(market - debt, "Equity = Estimated Market Value - Outstanding Debt", estimated_market_value=market, outstanding_debt=debt) if market is not None and debt is not None else _unknown(market_error or debt_error or "Verified market value and debt are required")
    mao_percent, mao_percent_error = _number(data.assumptions.mao_percentage, "MAO percentage")
    desired_profit, desired_profit_error = _number(data.assumptions.desired_profit, "Desired profit")
    mao = _calculated(arv * mao_percent - repair - desired_profit, "MAO = ARV × MAO_PERCENTAGE - REPAIR_COST - DESIRED_PROFIT", arv=arv, mao_percentage=mao_percent, repair_cost=repair, desired_profit=desired_profit) if None not in (arv, mao_percent, repair, desired_profit) else _unknown(arv_error or mao_percent_error or repair_error or desired_profit_error or "Required MAO inputs are missing")
    spread = _calculated(assignment - purchase, "Wholesale Spread = Expected Assignment Price - Purchase Contract Price", expected_assignment_price=assignment, purchase_contract_price=purchase) if assignment is not None and purchase is not None else _unknown(assignment_error or purchase_error or "Contract and assignment values are required")
    margin = _calculated((assignment - purchase) / purchase * 100, "Wholesale Margin % = Wholesale Spread / Purchase Contract Price × 100", wholesale_spread=assignment - purchase, purchase_contract_price=purchase) if assignment is not None and purchase not in (None, 0) else _unknown("Purchase contract price must be available and non-zero")
    transaction, transaction_error = _number(data.assumptions.transaction_costs, "Transaction costs")
    holding, holding_error = _number(data.assumptions.holding_costs, "Holding costs")
    financing, financing_error = _number(data.assumptions.financing_costs, "Financing costs")
    other, other_error = _number(data.assumptions.other_costs, "Other costs")
    flip = _calculated(sale - purchase - repair - transaction - holding - financing - other, "Flip Profit = Expected Sale Price - Purchase Price - Repair Cost - Transaction Costs - Holding Costs - Financing Costs - Other Costs", expected_sale_price=sale, purchase_price=purchase, repair_cost=repair, transaction_costs=transaction, holding_costs=holding, financing_costs=financing, other_costs=other) if all(value is not None for value in (sale, purchase, repair, transaction, holding, financing, other)) else _unknown(sale_error or purchase_error or repair_error or transaction_error or holding_error or financing_error or other_error or "Every explicit flip-cost component is required")
    invested, invested_error = _number(data.assumptions.total_invested_capital, "Total invested capital")
    roi = _calculated(profit / invested * 100, "ROI % = Net Profit / Total Invested Capital × 100", net_profit=profit, total_invested_capital=invested) if profit is not None and invested not in (None, 0) else _unknown(profit_error or invested_error or "Total invested capital must be available and non-zero")
    price_vs_arv = _calculated(asking / arv * 100, "Price vs ARV % = Asking Price / ARV × 100", asking_price=asking, arv=arv) if asking is not None and arv not in (None, 0) else _unknown(asking_error or arv_error or "ARV must be available and non-zero")
    return AnalysisResult(arv=MetricResult(state=ResultState.CALCULATED, value=arv, formula="ARV = Weighted Comparable Value") if arv is not None else _unknown(arv_error or "Qualified comparables are unavailable", ResultState.INSUFFICIENT_DATA), equity=equity, mao=mao, wholesale_spread=spread, wholesale_margin=margin, flip_profit=flip, roi=roi, price_vs_comps=_unknown("Qualified comparable weights and selection configuration are required", ResultState.CONFIGURATION_REQUIRED), price_vs_arv=price_vs_arv, deal_score=_unknown("Configurable deterministic deal-score weights are required", ResultState.CONFIGURATION_REQUIRED), risk_score=_unknown("Configurable deterministic risk thresholds are required", ResultState.CONFIGURATION_REQUIRED), classification=_unknown("Final classification requires configured deterministic score and risk rules", ResultState.CONFIGURATION_REQUIRED), explanation=["Formula results are server-side CALCULATED_DATA.", "Missing inputs retain UNKNOWN or INSUFFICIENT_DATA status.", "AI cannot calculate, overwrite, or re-rank financial results."])
