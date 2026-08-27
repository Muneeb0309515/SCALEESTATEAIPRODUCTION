"""Deterministic deal pipeline rules from design-doc.md.

Persistence is deliberately separate: callers must record returned events in their
organization-scoped append-only activity log and create the snapshot atomically.
"""
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class DealStage(str, Enum):
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    RESEARCHING = "RESEARCHING"
    CONTACTED = "CONTACTED"
    FOLLOW_UP = "FOLLOW_UP"
    NEGOTIATING = "NEGOTIATING"
    OFFER_MADE = "OFFER_MADE"
    CONTRACT_PENDING = "CONTRACT_PENDING"
    UNDER_CONTRACT = "UNDER_CONTRACT"
    BUYER_SEARCH = "BUYER_SEARCH"
    BUYER_INTERESTED = "BUYER_INTERESTED"
    BUYER_SELECTED = "BUYER_SELECTED"
    ASSIGNMENT_PENDING = "ASSIGNMENT_PENDING"
    ASSIGNED = "ASSIGNED"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    DEAD = "DEAD"
    CANCELLED = "CANCELLED"


FORWARD_STAGES = [
    DealStage.NEW, DealStage.QUALIFIED, DealStage.RESEARCHING, DealStage.CONTACTED,
    DealStage.FOLLOW_UP, DealStage.NEGOTIATING, DealStage.OFFER_MADE,
    DealStage.CONTRACT_PENDING, DealStage.UNDER_CONTRACT, DealStage.BUYER_SEARCH,
    DealStage.BUYER_INTERESTED, DealStage.BUYER_SELECTED, DealStage.ASSIGNMENT_PENDING,
    DealStage.ASSIGNED, DealStage.CLOSING, DealStage.CLOSED,
]
TERMINAL_STAGES = {DealStage.DEAD, DealStage.CANCELLED, DealStage.CLOSED}


class TransitionInput(BaseModel):
    current_stage: DealStage
    new_stage: DealStage
    contract_price: float | None = Field(default=None, gt=0)
    closing_date: date | None = None
    analysis_snapshot: dict | None = None


class TransitionResult(BaseModel):
    allowed: bool
    status_code: int
    reason: str | None = None
    required_actions: list[str] = []


def validate_transition(data: TransitionInput) -> TransitionResult:
    """Validate an explicit stage change; UI clients cannot force a transition."""
    if data.current_stage in TERMINAL_STAGES:
        return TransitionResult(allowed=False, status_code=409, reason="Terminal deals cannot transition further")
    if data.new_stage in {DealStage.DEAD, DealStage.CANCELLED}:
        return TransitionResult(allowed=True, status_code=200, required_actions=["append_activity_log"])
    current_index = FORWARD_STAGES.index(data.current_stage)
    if data.new_stage not in FORWARD_STAGES or FORWARD_STAGES.index(data.new_stage) != current_index + 1:
        return TransitionResult(allowed=False, status_code=409, reason="Only documented sequential transitions are allowed")
    actions = ["append_activity_log", "append_stage_history"]
    if data.new_stage == DealStage.UNDER_CONTRACT:
        if data.contract_price is None or data.closing_date is None:
            return TransitionResult(allowed=False, status_code=422, reason="Under Contract requires a contract price and closing date")
        if not data.analysis_snapshot:
            return TransitionResult(allowed=False, status_code=422, reason="Under Contract requires an immutable deterministic analysis snapshot")
        actions.extend([
            "create_immutable_analysis_snapshot", "create_transaction_record", "create_buyer_search_task",
            "queue_deterministic_buyer_matching", "send_user_notification",
        ])
    return TransitionResult(allowed=True, status_code=200, required_actions=actions)
