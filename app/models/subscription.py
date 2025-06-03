# app/models/subscription.py
from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, Integer, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import UUIDModel
import enum

class ResetIntervalEnum(str, enum.Enum):
    ONE_TIME = "annual"
    MONTHLY = "monthly"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"

class SubscriptionPlan(UUIDModel):
    __tablename__ = "subscription_plans"

    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    duration_days = Column(Integer, nullable=False)
    free_trial_calls = Column(Integer, nullable=False, default=0)
    reset_interval = Column(Enum(ResetIntervalEnum), nullable=False)
    features = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_subscriptions = relationship("UserSubscription", back_populates="plan")

class UserSubscription(UUIDModel):
    __tablename__ = "user_subscriptions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False)
    start_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    payment_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="user_subscriptions")