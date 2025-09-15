from pydantic import BaseModel
from typing import Optional
from app.models.subscription import PlanType


class SubscriptionCreate(BaseModel):
    plan: PlanType


class SubscriptionOut(BaseModel):
    id: int
    plan: PlanType
    is_active: bool

    class Config:
        from_attributes = True


class PurchaseCreate(BaseModel):
    course_id: int
    amount: float
    currency: str = "usd"


class PurchaseOut(BaseModel):
    id: int
    course_id: int
    amount: float
    currency: str
