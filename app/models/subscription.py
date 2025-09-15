from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, DateTime, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class PlanType(str, enum.Enum):
    monthly = "monthly"
    annual = "annual"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(Enum(PlanType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    stripe_subscription_id = Column(String(255), nullable=True)

    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="subscriptions")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="usd", nullable=False)
    stripe_payment_intent_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
