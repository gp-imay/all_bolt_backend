# app/services/subscription_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import logging
import razorpay
import hmac
import hashlib

from app.models.subscription import UserSubscription, SubscriptionPlan, SubscriptionStatus
from app.models.users import User
from app.config import settings
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.razorpay_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    @staticmethod
    def get_active_subscription(
        db: Session,
        user_id: UUID
    ) -> Optional[UserSubscription]:
        """Get user's active subscription"""
        return db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE,
                UserSubscription.expires_at > datetime.now()
            )
        ).first()

    @staticmethod
    def get_user_plan(
        db: Session,
        user_id: UUID
    ) -> Optional[SubscriptionPlan]:
        """Get user's current plan (defaults to free if no active subscription)"""
        active_sub = SubscriptionService.get_active_subscription(db, user_id)
        
        if active_sub:
            return active_sub.plan
        
        # Return free plan
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.name == "free"
        ).first()

    @staticmethod
    def create_subscription(
        db: Session,
        user_id: UUID,
        plan_id: UUID,
        payment_reference: str,
        payment_metadata: Dict[str, Any]
    ) -> UserSubscription:
        """Create a new subscription"""
        # Get plan details
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription plan not found"
            )
        
        # Cancel any existing active subscriptions
        existing = db.query(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user_id,
                UserSubscription.status == SubscriptionStatus.ACTIVE
            )
        ).all()
        
        for sub in existing:
            sub.status = SubscriptionStatus.CANCELLED
            sub.cancelled_at = datetime.now()
        
        # Create new subscription
        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            start_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=plan.duration_days),
            payment_reference=payment_reference,
            payment_metadata=payment_metadata
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        return subscription

    def verify_razorpay_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """Verify Razorpay payment signature"""
        try:
            # Create expected signature
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                bytes(settings.RAZORPAY_KEY_SECRET, 'latin-1'),
                msg=bytes(message, 'latin-1'),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, razorpay_signature)
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return False

    @staticmethod
    def check_subscription_expiry(
        db: Session
    ) -> int:
        """Check and update expired subscriptions (run as cron job)"""
        expired = db.query(UserSubscription).filter(
            and_(
                UserSubscription.status == SubscriptionStatus.ACTIVE,
                UserSubscription.expires_at <= datetime.now()
            )
        ).all()
        
        for sub in expired:
            sub.status = SubscriptionStatus.EXPIRED
        
        db.commit()
        return len(expired)

    @staticmethod
    def get_subscription_status(
        db: Session,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get detailed subscription status for a user"""
        active_sub = SubscriptionService.get_active_subscription(db, user_id)
        current_plan = SubscriptionService.get_user_plan(db, user_id)
        
        if active_sub:
            return {
                "has_active_subscription": True,
                "subscription": {
                    "id": str(active_sub.id),
                    "plan": active_sub.plan.name,
                    "display_name": active_sub.plan.display_name,
                    "status": active_sub.status.value,
                    "expires_at": active_sub.expires_at.isoformat(),
                    "days_remaining": (active_sub.expires_at - datetime.now()).days
                }
            }
        
        return {
            "has_active_subscription": False,
            "subscription": None,
            "current_plan": current_plan.name if current_plan else "free"
        }