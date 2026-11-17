import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        actor: str = "USER",
        trip_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        input_data: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Records an audit log entry."""
        log_entry = AuditLog(
            trip_id=trip_id,
            user_id=user_id,
            action=action,
            actor=actor,
            input_data=input_data or {},
            result=result or {}
        )
        db.add(log_entry)
        await db.flush()
        logger.info(f"AUDIT [{action}] Actor={actor} Trip={trip_id} User={user_id}")
        return log_entry
