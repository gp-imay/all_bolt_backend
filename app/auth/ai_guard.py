# app/auth/ai_guard.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.subscription_service import SubscriptionService
from app.services.usage_service import UsageService
from app.models.usage import AICallTypeEnum
from app.config import settings

async def get_ai_call_guard(
    # call_type: AICallTypeEnum,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Guard dependency that checks AI usage limits
    """
    # Check if user has active subscription
    active_subscription = SubscriptionService.get_active_subscription(db, current_user.id)
    
    if active_subscription:
        # Paid users have unlimited access
        return current_user
    
    # Free tier - check usage limits
    remaining_calls = UsageService.get_remaining_free_calls(db, current_user.id)
    
    if remaining_calls <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "free_tier_limit_exceeded",
                "message": "You've reached your free tier limit",
                "calls_remaining": 0,
                "upgrade_url": "/pricing/status"
            }
        )
    
    return current_user

# def get_ai_call_guard(call_type: AICallTypeEnum):
#     async def guard(
#         current_user = Depends(get_current_user),
#         db: Session = Depends(get_db)
#     ):
#         """
#         Guard dependency that checks AI usage limits
#         """
#         print("Coming from here")
        
#         # Check if user has active subscription
#         active_subscription = SubscriptionService.get_active_subscription(db, current_user.id)
        
#         if active_subscription:
#             # Paid users have unlimited access
#             return current_user
        
#         # Free tier - check usage limits
#         remaining_calls = UsageService.get_remaining_free_calls(db, current_user.id)
        
#         if remaining_calls <= 0:
#             raise HTTPException(
#                 status_code=status.HTTP_402_PAYMENT_REQUIRED,
#                 detail={
#                     "error": "free_tier_limit_exceeded",
#                     "message": "You've reached your free tier limit",
#                     "calls_remaining": 0,
#                     "upgrade_url": "/pricing/status"
#                 }
#             )
        
#         return current_user
    
#     return guard
