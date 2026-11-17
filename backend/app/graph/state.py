import uuid
from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field
from app.schemas.trip import TravelIntent


class AgentState(TypedDict):
    """LangGraph orchestrator state schema."""
    trip_id: str
    user_id: str
    user_message: str
    conversation_id: Optional[str]
    intent: Optional[Dict[str, Any]]
    missing_fields: List[str]
    current_goal: str
    next_step: Optional[str]
    reply: str
    recommendations: Optional[List[Dict[str, Any]]]
    itineraries: Optional[List[Dict[str, Any]]]
    selected_itinerary_id: Optional[str]
    pending_action: Optional[Dict[str, Any]]
    context: Dict[str, Any]
    error: Optional[str]
