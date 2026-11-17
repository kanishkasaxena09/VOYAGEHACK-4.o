import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    ConfirmationRequiredException,
    DuplicateActionException,
    ExpiredConfirmationException,
    ResourceNotFoundException,
    ValidationException,
)
from app.models.pending_action import ActionStatus, ActionType, PendingAction
from app.services.audit_service import AuditService


class ConfirmationService:
    DEFAULT_EXPIRY_MINUTES: int = 20

    @classmethod
    async def create_pending_action(
        cls,
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        action_type: str,
        estimated_amount: float,
        details: Dict[str, Any],
        currency: str = "INR",
        idempotency_key: Optional[str] = None,
        expiry_minutes: Optional[int] = None
    ) -> PendingAction:
        key = idempotency_key or f"idem-{action_type.lower()}-{uuid.uuid4().hex[:12]}"

        # Check existing action with this key
        existing_stmt = select(PendingAction).where(PendingAction.idempotency_key == key)
        res = await db.execute(existing_stmt)
        existing = res.scalars().first()
        if existing:
            if existing.status in [ActionStatus.CONFIRMED, ActionStatus.EXECUTING, ActionStatus.COMPLETED]:
                raise DuplicateActionException(action_type, key)
            return existing

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expiry_minutes or cls.DEFAULT_EXPIRY_MINUTES)

        pending = PendingAction(
            trip_id=trip_id,
            user_id=user_id,
            action_type=action_type,
            status=ActionStatus.AWAITING_CONFIRMATION,
            idempotency_key=key,
            estimated_amount=round(estimated_amount, 2),
            currency=currency,
            expires_at=expires_at,
            details=details
        )
        db.add(pending)
        await db.flush()

        await AuditService.log_action(
            db=db,
            action="PENDING_ACTION_CREATED",
            actor="SYSTEM",
            trip_id=trip_id,
            user_id=user_id,
            input_data={"action_type": action_type, "estimated_amount": estimated_amount},
            result={"pending_action_id": str(pending.id), "status": pending.status}
        )

        return pending

    @classmethod
    async def get_and_validate_for_execution(
        cls,
        db: AsyncSession,
        pending_action_id: uuid.UUID,
        user_id: uuid.UUID,
        idempotency_key: str
    ) -> PendingAction:
        stmt = select(PendingAction).where(
            PendingAction.id == pending_action_id,
            PendingAction.user_id == user_id
        )
        res = await db.execute(stmt)
        action = res.scalars().first()

        if not action:
            raise ResourceNotFoundException("PendingAction", pending_action_id)

        # Idempotency check
        if action.status == ActionStatus.COMPLETED:
            raise DuplicateActionException(action.action_type, idempotency_key)

        if action.status == ActionStatus.EXECUTING:
            raise ValidationException(f"Action '{action.action_type}' is currently executing.")

        # Expiry check
        now = datetime.now(timezone.utc)
        expiry = action.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if now > expiry:
            action.status = ActionStatus.EXPIRED
            await db.flush()
            raise ExpiredConfirmationException(str(pending_action_id))

        if action.status != ActionStatus.AWAITING_CONFIRMATION:
            raise ValidationException(f"Action cannot be confirmed from status '{action.status}'.")

        # Mark confirmed and executing
        action.status = ActionStatus.CONFIRMED
        await db.flush()
        action.status = ActionStatus.EXECUTING
        await db.flush()

        return action

    @classmethod
    async def mark_completed(
        cls,
        db: AsyncSession,
        action: PendingAction,
        result_details: Dict[str, Any]
    ) -> None:
        action.status = ActionStatus.COMPLETED
        action.details = {**action.details, "result": result_details}
        await db.flush()

    @classmethod
    async def mark_failed(
        cls,
        db: AsyncSession,
        action: PendingAction,
        error_message: str
    ) -> None:
        action.status = ActionStatus.FAILED
        action.details = {**action.details, "error": error_message}
        await db.flush()
