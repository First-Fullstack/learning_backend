from pydantic import BaseModel
from typing import Optional, List


class SubscriptionPlanOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price_monthly: int
    price_yearly: int
    features: List[str]
    is_active: bool

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    plan_id: int


class SubscriptionOut(BaseModel):
    id: int
    plan_id: int
    status: str


class PurchaseCreate(BaseModel):
    course_id: int
    amount: float
    currency: str = "usd"


class PurchaseOut(BaseModel):
    id: int
    course_id: int
    amount: float
    currency: str


class SubscribeIn(BaseModel):
    plan_id: int
    payment_method_id: str


class SubscribeOut(BaseModel):
    subscription_id: str
    status: str


class ChangePlanIn(BaseModel):
    new_plan_id: int


class ChangePlanOut(BaseModel):
    subscription_id: str
    status: str
