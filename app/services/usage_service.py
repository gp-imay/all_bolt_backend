# app/services/usage_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import logging
import traceback

from app.models.usage import AIUsageLog, AICallTypeEnum
from app.models.subscription import ResetIntervalEnum, SubscriptionPlan
from app.config import settings

logger = logging.getLogger(__name__)

class UsageService:
    @staticmethod
    def log_ai_call(
        db: Session,
        user_id: UUID,
        call_type: AICallTypeEnum,
        script_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> AIUsageLog:
        """Log an AI API call"""
        try:
            usage_log = AIUsageLog(
                user_id=user_id,
                call_type=call_type,
                script_id=script_id,
                metadata=metadata
            )
            db.add(usage_log)
            db.commit()
            db.refresh(usage_log)
            print("Afterr")
            return usage_log
        except Exception as e:
            logger.info(e)
            logger.info("-"*100)
            logger.info(traceback.format_exc())

    @staticmethod
    def get_free_usage_count(
        db: Session,
        user_id: UUID,
        reset_interval: ResetIntervalEnum = None
    ) -> int:
        """Count AI usage for free tier users"""
        # Use config default if not specified
        if not reset_interval:
            reset_interval = ResetIntervalEnum(settings.FREE_TIER_RESET_INTERVAL)
            
        query = db.query(func.count(AIUsageLog.id)).filter(
            AIUsageLog.user_id == user_id
        )
        
        if reset_interval == ResetIntervalEnum.MONTHLY:
            # Count only this month's usage
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(AIUsageLog.timestamp >= start_of_month)
        # else: one_time means count all usage ever
        val = query.scalar()
        return val or 0

    @staticmethod
    def get_remaining_free_calls(
        db: Session,
        user_id: UUID,
        free_limit: int = None
    ) -> int:
        """Get remaining free calls for a user"""
        if not free_limit:
            free_limit = settings.FREE_TIER_CALL_LIMIT
        print(free_limit)
        usage_count = UsageService.get_free_usage_count(db, user_id)
        print(usage_count)
        return max(0, free_limit - usage_count)

    @staticmethod
    def get_usage_summary(
        db: Session,
        user_id: UUID,
        days: int = 30
    ) -> dict:
        """Get usage summary for analytics"""
        since = datetime.now() - timedelta(days=days)
        
        usage_by_type = db.query(
            AIUsageLog.call_type,
            func.count(AIUsageLog.id).label('count')
        ).filter(
            and_(
                AIUsageLog.user_id == user_id,
                AIUsageLog.timestamp >= since
            )
        ).group_by(AIUsageLog.call_type).all()
        
        return {
            "period_days": days,
            "total_calls": sum(u.count for u in usage_by_type),
            "by_type": {u.call_type.value: u.count for u in usage_by_type}
        }