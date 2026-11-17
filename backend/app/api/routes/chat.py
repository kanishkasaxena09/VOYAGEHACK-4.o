import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db, get_user_trip
from app.graph.graph import travel_orchestrator
from app.models.conversation import Conversation, ConversationMessage
from app.models.trip import Trip
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationHistoryMessage,
    ConversationHistoryResponse,
    ConversationalStateInfo,
)
from app.schemas.common import APIResponse
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/trips/{trip_id}", tags=["Conversation"])


@router.post("/chat", response_model=APIResponse[ChatMessageResponse])
async def chat_with_agent(
    trip_id: uuid.UUID,
    req: ChatMessageRequest,
    trip: Trip = Depends(get_user_trip),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Get or create conversation in trip memory
    conversation = await MemoryService.get_or_create_conversation(db, trip.id)

    # 2. Append User Message
    await MemoryService.append_message(
        db=db,
        conversation_id=conversation.id,
        sender="USER",
        message=req.message
    )

    # 3. Execute LangGraph Orchestrator
    result_state = await travel_orchestrator.run(
        db=db,
        trip_id=str(trip.id),
        user_id=str(user.id),
        user_message=req.message,
        conversation_id=str(conversation.id)
    )

    reply_text = result_state.get("reply", "I am working on your travel request.")

    # 4. Append Agent Message
    await MemoryService.append_message(
        db=db,
        conversation_id=conversation.id,
        sender="AGENT",
        message=reply_text,
        intent=result_state.get("current_goal"),
        state_snapshot=result_state.get("context")
    )

    state_info = ConversationalStateInfo(
        current_goal=result_state.get("current_goal", "conversational"),
        missing_information=result_state.get("missing_fields", []),
        pending_action=str(result_state.get("pending_action", {}).get("id")) if result_state.get("pending_action") else None,
        next_step=result_state.get("next_step"),
        current_agent=result_state.get("current_goal"),
        context=result_state.get("context", {})
    )

    chat_resp = ChatMessageResponse(
        reply=reply_text,
        trip_id=trip.id,
        state=state_info,
        recommendations=result_state.get("recommendations"),
        itineraries=result_state.get("itineraries"),
        pending_action_details=result_state.get("pending_action")
    )

    return APIResponse.ok(
        data=chat_resp,
        message="Message processed successfully."
    )


@router.get("/conversation", response_model=APIResponse[ConversationHistoryResponse])
async def get_conversation_history(
    trip_id: uuid.UUID,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    conv = await MemoryService.get_or_create_conversation(db, trip.id)
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.created_at.asc())
    )
    res = await db.execute(stmt)
    messages = res.scalars().all()

    return APIResponse.ok(
        data=ConversationHistoryResponse(
            trip_id=trip.id,
            conversation_id=conv.id,
            messages=[ConversationHistoryMessage.model_validate(m) for m in messages]
        ),
        message="Conversation history retrieved."
    )
