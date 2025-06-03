# app/routers/pricing.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime
import logging



from app.database import get_db
from app.auth.dependencies import get_current_user
from app.schemas.user import User
from app.services.subscription_service import SubscriptionService
from app.services.usage_service import UsageService
from app.models.subscription import SubscriptionPlan, ResetIntervalEnum
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class PricingStatusResponse(BaseModel):
    calls_remaining: Optional[int]
    free_limit: int
    period_reset: str
    subscription: Optional[dict]
    usage_summary: Optional[dict]

class PaymentReportRequest(BaseModel):
    plan_id: UUID
    razorpay_order_id: str = Field(..., description="Razorpay order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID")
    razorpay_signature: str = Field(..., description="Razorpay signature for verification")
    amount: float = Field(..., description="Payment amount in INR")

class PaymentReportResponse(BaseModel):
    success: bool
    subscription_id: Optional[UUID]
    message: str
    expires_at: Optional[datetime]

@router.get("/status", response_model=PricingStatusResponse)
async def get_pricing_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's subscription and usage status"""
    subscription_status = SubscriptionService.get_subscription_status(db, current_user.id)
    usage_summary = UsageService.get_usage_summary(db, current_user.id, days=30)
    
    # Calculate remaining calls
    if subscription_status["has_active_subscription"]:
        calls_remaining = None  # Unlimited for paid users
    else:
        calls_remaining = UsageService.get_remaining_free_calls(db, current_user.id)
    
    return PricingStatusResponse(
        calls_remaining=calls_remaining,
        free_limit=settings.FREE_TIER_CALL_LIMIT,
        period_reset=settings.FREE_TIER_RESET_INTERVAL,
        subscription=subscription_status.get("subscription"),
        usage_summary=usage_summary
    )

@router.post("/report-payment", response_model=PaymentReportResponse)
async def report_payment(
    payment_data: PaymentReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report a payment from Razorpay and activate subscription"""
    subscription_service = SubscriptionService()
    
    # Verify payment with Razorpay
    is_valid = subscription_service.verify_razorpay_payment(
        payment_data.razorpay_order_id,
        payment_data.razorpay_payment_id,
        payment_data.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    try:
        # Create subscription
        subscription = SubscriptionService.create_subscription(
            db=db,
            user_id=current_user.id,
            plan_id=payment_data.plan_id,
            payment_reference=payment_data.razorpay_payment_id,
            payment_metadata={
                "order_id": payment_data.razorpay_order_id,
                "payment_id": payment_data.razorpay_payment_id,
                "amount": payment_data.amount,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return PaymentReportResponse(
            success=True,
            subscription_id=subscription.id,
            message="Subscription activated successfully",
            expires_at=subscription.expires_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate subscription"
        )

@router.get("/plans", response_model=List[dict])
async def get_subscription_plans(
    db: Session = Depends(get_db)
):
    """Get all available subscription plans"""
    plans = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.is_active is True
    ).all()
    
    return [
        {
            "id": str(plan.id),
            "name": plan.name,
            "display_name": plan.display_name,
            "price": float(plan.price),
            "currency": plan.currency,
            "duration_days": plan.duration_days,
            "features": plan.features
        }
        for plan in plans
    ]