"""Deterministic buyer matching based on the weights specified in design-doc.md."""
from .schemas import BuyerCriteria, BuyerMatch, DealCandidate, MatchConfiguration


def _range_score(value: float | None, low: float | None, high: float | None) -> float | None:
    if value is None or low is None or high is None:
        return None
    return 1.0 if low <= value <= high else 0.0


def match_buyer(deal: DealCandidate, buyer: BuyerCriteria, configuration: MatchConfiguration) -> BuyerMatch:
    reasons: list[str] = []
    failures: list[str] = []
    market = 1.0 if deal.market in buyer.markets else 0.0
    zip_code = 1.0 if deal.zip_code in buyer.zip_codes else 0.0
    property_type = 1.0 if deal.property_type in buyer.property_types else 0.0
    price = _range_score(deal.purchase_price, buyer.price_min, buyer.price_max)
    arv = _range_score(deal.arv, buyer.arv_min, buyer.arv_max)
    spread = 1.0 if deal.wholesale_spread is not None and buyer.minimum_spread is not None and deal.wholesale_spread >= buyer.minimum_spread else 0.0
    financing = 1.0 if (not deal.requires_financing and buyer.cash_only) or (deal.requires_financing and buyer.financing_available) or (not deal.requires_financing and buyer.financing_available) else 0.0
    activity = deal.buyer_activity_score
    scores = {"market": market, "zip": zip_code, "property_type": property_type, "price": price if price is not None else 0.0, "arv": arv if arv is not None else 0.0, "spread": spread, "financing": financing, "activity": activity if activity is not None else 0.0}
    checks = [(market, f"Buyer operates in {deal.market}", "Market not included"), (zip_code, f"Buyer includes ZIP {deal.zip_code}", "ZIP not included"), (property_type, f"Buyer accepts {deal.property_type}", "Property type not accepted"), (price, "Purchase price falls within buyer range", "Purchase price is unavailable or outside range"), (arv, "ARV falls within buyer range", "ARV is unavailable or outside range"), (spread, "Deal spread meets buyer minimum", "Spread is unavailable or below buyer minimum"), (financing, "Financing capability is compatible", "Financing capability is incompatible"), (activity, "Buyer activity score is recorded", "Buyer activity evidence is unavailable")]
    for score, reason, failure in checks:
        (reasons if score not in (None, 0.0) else failures).append(reason if score not in (None, 0.0) else failure)
    weights = [configuration.market_weight, configuration.zip_weight, configuration.property_type_weight, configuration.price_weight, configuration.arv_weight, configuration.spread_weight, configuration.financing_weight, configuration.activity_weight]
    weighted = sum([market * configuration.market_weight, zip_code * configuration.zip_weight, property_type * configuration.property_type_weight, scores["price"] * configuration.price_weight, scores["arv"] * configuration.arv_weight, spread * configuration.spread_weight, financing * configuration.financing_weight, scores["activity"] * configuration.activity_weight]) / sum(weights)
    confidence = "high" if weighted >= configuration.high_confidence_threshold else "medium" if weighted >= configuration.medium_confidence_threshold else "low"
    return BuyerMatch(buyer_id=buyer.buyer_id, match_score=round(weighted, 6), confidence=confidence, factor_scores=scores, match_reasons=reasons, failed_criteria=failures, configuration=configuration)
