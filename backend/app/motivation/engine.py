"""Explicit motivation rules only; scores require separately configured weights."""
from .schemas import MotivationInput, MotivationResult, MotivationSignal


def detect_motivation_signals(data: MotivationInput) -> MotivationResult:
    signals: list[MotivationSignal] = []
    def add(signal_type: str, evidence: str):
        signals.append(MotivationSignal(signal_type=signal_type, evidence=evidence, source=data.source, confidence=data.source_confidence, detected_at=data.detected_at))
    if data.estimated_equity is not None and data.estimated_market_value is not None and data.estimated_equity / data.estimated_market_value > .5:
        add("HIGH_EQUITY", "Estimated equity exceeds 50% of verified or estimated market value")
    if data.ownership_duration_years is not None and data.ownership_duration_years > 10:
        add("LONG_OWNERSHIP", "Ownership duration exceeds 10 years")
    for value, signal_type, description in [(data.tax_delinquent, "TAX_DELINQUENT", "Public records indicate tax delinquency"), (data.foreclosure_related, "FORECLOSURE_RELATED", "Public records indicate foreclosure-related status"), (data.vacant, "VACANT", "Property appears vacant"), (data.expired_listing, "EXPIRED_LISTING", "Listing is expired"), (data.withdrawn_listing, "WITHDRAWN_LISTING", "Listing is withdrawn"), (data.probate_related, "PROBATE_RELATED", "Public records indicate probate-related status"), (data.entity_ownership, "ENTITY_OWNERSHIP", "Owner is an entity"), (data.distressed_property, "DISTRESSED_PROPERTY", "Property condition evidence indicates distress")]:
        if value is True:
            add(signal_type, description)
    if data.days_on_market is not None and data.days_on_market > 180:
        add("LONG_DOM", "Days on market exceeds 180")
    return MotivationResult(signals=signals, motivation_score_state="CONFIGURATION_REQUIRED", confidence_state="CONFIGURATION_REQUIRED", explanation="Signals are deterministic and evidence-traceable. Weighted motivation scoring and confidence classification require configured factor weights and thresholds.")
