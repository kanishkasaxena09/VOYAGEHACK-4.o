import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's natural language input message")


class ConversationalStateInfo(BaseModel):
    current_goal: str
    missing_information: List[str] = Field(default_factory=list)
    pending_action: Optional[str] = None
    next_step: Optional[str] = None
    current_agent: Optional[str] = None
    context: Optional[dict] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    reply: str
    trip_id: uuid.UUID
    state: ConversationalStateInfo
    recommendations: Optional[List[dict]] = None
    itineraries: Optional[List[dict]] = None
    pending_action_details: Optional[dict] = None


class ConversationHistoryMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender: str
    message: str
    intent: Optional[str] = None
    created_at: datetime


class ConversationHistoryResponse(BaseModel):
    trip_id: uuid.UUID
    conversation_id: uuid.UUID
    messages: List[ConversationHistoryMessage]
