from typing import Any, Dict
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession
from app.graph.nodes import (
    condition_check_missing,
    node_ask_followup,
    node_confirmation_gate,
    node_destination_discovery,
    node_disruption_handling,
    node_extract_intent,
    node_itinerary_planning,
    node_partial_replanning,
    node_trip_management,
    node_update_memory,
)
from app.graph.state import AgentState


class TravelGraphOrchestrator:
    def __init__(self):
        self._compiled_graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(AgentState)

        # Base node wrappers that inject DB session from state context
        async def run_extract_intent(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_extract_intent(state, db)

        async def run_update_memory(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_update_memory(state, db)

        async def run_ask_followup(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_ask_followup(state, db)

        async def run_destination_discovery(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_destination_discovery(state, db)

        async def run_itinerary_planning(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_itinerary_planning(state, db)

        async def run_partial_replanning(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_partial_replanning(state, db)

        async def run_confirmation_gate(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_confirmation_gate(state, db)

        async def run_disruption_handling(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_disruption_handling(state, db)

        async def run_trip_management(state: AgentState):
            db: AsyncSession = state["context"]["db"]
            return await node_trip_management(state, db)

        # Register nodes
        builder.add_node("extract_intent", run_extract_intent)
        builder.add_node("update_memory", run_update_memory)
        builder.add_node("ask_followup", run_ask_followup)
        builder.add_node("destination_discovery", run_destination_discovery)
        builder.add_node("itinerary_planning", run_itinerary_planning)
        builder.add_node("partial_replanning", run_partial_replanning)
        builder.add_node("confirmation_gate", run_confirmation_gate)
        builder.add_node("disruption_handling", run_disruption_handling)
        builder.add_node("trip_management", run_trip_management)

        # Add graph edges
        builder.add_edge(START, "extract_intent")
        builder.add_edge("extract_intent", "update_memory")

        builder.add_conditional_edges(
            "update_memory",
            condition_check_missing,
            {
                "ask_followup": "ask_followup",
                "destination_discovery": "destination_discovery",
                "itinerary_planning": "itinerary_planning",
                "partial_replanning": "partial_replanning",
                "confirmation_gate": "confirmation_gate",
                "disruption_handling": "disruption_handling",
                "trip_management": "trip_management"
            }
        )

        builder.add_edge("ask_followup", END)
        builder.add_edge("destination_discovery", END)
        builder.add_edge("itinerary_planning", END)
        builder.add_edge("partial_replanning", END)
        builder.add_edge("confirmation_gate", END)
        builder.add_edge("disruption_handling", END)
        builder.add_edge("trip_management", END)

        return builder.compile()

    async def run(
        self,
        db: AsyncSession,
        trip_id: str,
        user_id: str,
        user_message: str,
        conversation_id: str | None = None
    ) -> Dict[str, Any]:
        initial_state: AgentState = {
            "trip_id": trip_id,
            "user_id": user_id,
            "user_message": user_message,
            "conversation_id": conversation_id,
            "intent": None,
            "missing_fields": [],
            "current_goal": "process_user_message",
            "next_step": None,
            "reply": "",
            "recommendations": None,
            "itineraries": None,
            "selected_itinerary_id": None,
            "pending_action": None,
            "context": {"db": db},
            "error": None
        }

        final_state = await self._compiled_graph.ainvoke(initial_state)

        # Remove raw non-serializable objects from output
        out = dict(final_state)
        if "context" in out and "db" in out["context"]:
            del out["context"]["db"]

        return out


travel_orchestrator = TravelGraphOrchestrator()
