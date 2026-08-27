from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class SellerCreate(BaseModel):
    property_id: str | None = None
    owner_id: str | None = None
    name: str = Field(min_length=1, max_length=250)
    email: str | None = None
    phone: str | None = None
    contact_classification: Literal["SOURCE_DATA", "USER_INPUT"]
    status: str = Field(default="NEW", max_length=80)
    next_follow_up_date: datetime | None = None


class BuyerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=250)
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    status: Literal["new", "active", "qualified", "inactive", "blacklisted"] = "new"


class DealCreate(BaseModel):
    property_id: str
    owner_id: str | None = None
    seller_id: str | None = None
    estimated_purchase_price: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=10000)


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    filters: dict


class TaskCreate(BaseModel):
    deal_id: str | None = None
    task_type: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    due_date: datetime | None = None
