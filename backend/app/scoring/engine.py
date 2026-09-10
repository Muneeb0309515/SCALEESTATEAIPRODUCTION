"""Configurable deterministic scoring; no proprietary weights or thresholds are invented."""
from .schemas import ClassificationConfiguration, ClassificationResult, WeightedScoreConfiguration, WeightedScoreInput


def calculate_weighted_score(score_input: WeightedScoreInput, configuration: WeightedScoreConfiguration) -> float:
    missing = set(configuration.weights) - set(score_input.factors)
    extra = set(score_input.factors) - set(configuration.weights)
    if missing or extra:
        raise ValueError(f"Score factors must exactly match configured weights; missing={sorted(missing)} extra={sorted(extra)}")
    return round(sum(score_input.factors[name] * weight for name, weight in configuration.weights.items()), 6)


def calculate_final_classification(deal_score: float | None, risk_score: float | None, configuration: ClassificationConfiguration | None) -> ClassificationResult:
    if deal_score is None or risk_score is None or configuration is None:
        return ClassificationResult(state="CONFIGURATION_REQUIRED", label="UNKNOWN", reason="Final classification requires deterministic deal score, risk score, and configured thresholds")
    if risk_score > configuration.caution_risk_maximum:
        return ClassificationResult(state="CALCULATED", label="HIGH_RISK", reason="Risk score exceeds the configured caution maximum")
    if deal_score >= configuration.strong_deal_score_minimum and risk_score <= configuration.acceptable_risk_maximum:
        return ClassificationResult(state="CALCULATED", label="STRONG_DEAL", reason="Deal score and risk score meet configured strong-deal thresholds")
    if deal_score >= configuration.moderate_deal_score_minimum:
        return ClassificationResult(state="CALCULATED", label="MODERATE_DEAL", reason="Deal score meets the configured moderate threshold")
    return ClassificationResult(state="CALCULATED", label="WEAK_DEAL", reason="Deal score is below the configured moderate threshold")
