"""Comparable calculations constrained to DETERMINISTIC_DEAL_ANALYSIS_ENGINE.md."""
from statistics import median
from .schemas import ComparableAnalysis, ComparableCandidate, ComparableConfiguration, ComparableReview


def _age_days(candidate: ComparableCandidate, configuration: ComparableConfiguration) -> int:
    return (configuration.search_date - candidate.sale_date).days


def _score(candidate: ComparableCandidate, configuration: ComparableConfiguration) -> float:
    return (candidate.distance_score * configuration.distance_weight) + (candidate.recency_score * configuration.recency_weight) + (candidate.similarity_score * configuration.similarity_weight) + (candidate.quality_score * configuration.quality_weight)


def analyze_comparables(candidates: list[ComparableCandidate], configuration: ComparableConfiguration) -> ComparableAnalysis:
    initially_eligible: list[ComparableCandidate] = []
    reviews: dict[str, ComparableReview] = {}
    for candidate in candidates:
        qualification_error = None
        if candidate.distance_miles > configuration.max_distance_miles:
            qualification_error = "Outside configured distance radius"
        elif _age_days(candidate, configuration) < 0 or _age_days(candidate, configuration) > configuration.max_sale_age_days:
            qualification_error = "Outside configured sale-recency window"
        elif candidate.living_area_deviation > configuration.max_living_area_deviation:
            qualification_error = "Outside configured living-area tolerance"
        if qualification_error:
            reviews[candidate.comparable_id] = ComparableReview(comparable_id=candidate.comparable_id, eligible=False, excluded_reason=qualification_error)
        else:
            initially_eligible.append(candidate)

    prices = [candidate.sale_price for candidate in initially_eligible]
    median_price = median(prices) if prices else None
    deviations = [abs(price - median_price) for price in prices] if median_price is not None else []
    mad = median(deviations) if deviations else None
    included: list[tuple[ComparableCandidate, float]] = []
    for candidate in initially_eligible:
        deviation = abs(candidate.sale_price - median_price) if median_price is not None else 0
        outlier_score = deviation / mad if mad not in (None, 0) else (0 if deviation == 0 else float("inf"))
        detected_outlier = outlier_score > configuration.outlier_mad_multiplier
        force_include = candidate.selected_by_user is True and bool(candidate.override_reason)
        force_exclude = candidate.selected_by_user is False and bool(candidate.override_reason)
        if force_exclude:
            reviews[candidate.comparable_id] = ComparableReview(comparable_id=candidate.comparable_id, eligible=True, excluded_reason="User excluded comparable", outlier=detected_outlier, outlier_score=outlier_score, user_override_applied=True, audit_event_required=True)
        elif detected_outlier and not force_include:
            reviews[candidate.comparable_id] = ComparableReview(comparable_id=candidate.comparable_id, eligible=True, excluded_reason="MAD outlier", outlier=True, outlier_score=outlier_score)
        else:
            score = _score(candidate, configuration)
            reviews[candidate.comparable_id] = ComparableReview(comparable_id=candidate.comparable_id, eligible=True, outlier=detected_outlier, outlier_score=outlier_score, comp_score=round(score, 6), user_override_applied=force_include, audit_event_required=force_include)
            included.append((candidate, score))

    total_score = sum(score for _, score in included)
    arv = None
    arv_state = "INSUFFICIENT_DATA" if len(included) < configuration.minimum_comparable_count else "CALCULATED"
    arv_reason = f"At least {configuration.minimum_comparable_count} qualified comparables are required" if arv_state == "INSUFFICIENT_DATA" else None
    if total_score > 0 and arv_state == "CALCULATED":
        arv = sum(candidate.sale_price * (score / total_score) for candidate, score in included)
        for candidate, score in included:
            reviews[candidate.comparable_id].effective_weight = round(score / total_score, 6)
    return ComparableAnalysis(reviews=[reviews[candidate.comparable_id] for candidate in candidates], weighted_arv=round(arv, 2) if arv is not None else None, arv_state=arv_state, arv_reason=arv_reason, included_comparable_count=len(included), median_sale_price=median_price, median_absolute_deviation=mad, configuration=configuration)
