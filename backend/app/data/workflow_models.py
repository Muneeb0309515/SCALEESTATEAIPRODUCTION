from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field


class OutreachCreate(BaseModel):
    contact_method: Literal["phone", "email", "mail", "visit"]
    message: str = Field(min_length=1, max_length=10000)
    subject: str | None = Field(default=None, max_length=500)
    send_requested: bool = False


class FollowUpCreate(BaseModel):
    deal_id: str | None = None
    follow_up_date: datetime
    notes: str = Field(min_length=1, max_length=2000)


class BuyerCriteriaUpdate(BaseModel):
    markets: list[str]
    zip_codes: list[str]
    property_types: list[str]
    price_range: dict | None = None
    arv_range: dict | None = None
    investment_strategy: str | None = None
    rehab_tolerance: str | None = None
    minimum_spread: float | None = None
    cash_only: bool = False
    financing_available: bool = False


class DistributionCreate(BaseModel):
    buyer_ids: list[str] = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=10000)


class DistributionResponse(BaseModel):
    response_status: Literal["opened", "responded", "offered", "selected", "rejected"]
    interest_level: Literal["not_interested", "maybe", "interested", "hot"] | None = None
    buyer_response_text: str | None = Field(default=None, max_length=10000)


class BuyerOfferCreate(BaseModel):
    offer_amount: float = Field(gt=0)
    closing_date: date | None = None
    contingencies: dict | None = None
    financing: str | None = None


class TransactionCreate(BaseModel):
    deal_id: str
    buyer_id: str
    exit_strategy: Literal["assignment", "double_close", "referral"]
    assignment_fee_target: float | None = None


class ClosingRecord(BaseModel):
    closing_price: float = Field(gt=0)
    closing_date: date
    closing_costs: float = Field(default=0, ge=0)
    final_net: float | None = None
