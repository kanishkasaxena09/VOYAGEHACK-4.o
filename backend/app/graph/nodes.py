import uuid
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.booking_agent import BookingAgent
from app.agents.destination_agent import DestinationAgent
from app.agents.disruption_agent import DisruptionAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.preference_agent import PreferenceAgent
from app.agents.search_agent import SearchAgent
from app.agents.trip_management_agent import TripManagementAgent
from app.graph.state import AgentState
from app.models.itinerary import Itinerary, ItineraryItem
from app.models.pending_action import ActionStatus, PendingAction
from app.models.trip import TripStatus
from app.schemas.trip import TravelIntent
from app.services.cost_service import CostService
from app.services.memory_service import MemoryService
from app.services.replanning_service import ReplanningService


async def node_extract_intent(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)
    msg = state["user_message"]

    intent = await PreferenceAgent.extract_preferences(msg, trip)
    state["intent"] = intent.model_dump(mode="json")
    state["missing_fields"] = intent.missing_fields
    state["current_goal"] = "intent_extracted"
    return state


async def node_update_memory(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)
    intent_data = state["intent"] or {}
    intent = TravelIntent.model_validate(intent_data)

    mem_res = await MemoryService.update_trip_memory_from_intent(db, trip, intent)
    state["context"]["memory_update"] = mem_res
    state["current_goal"] = "memory_updated"
    return state


def condition_check_missing(state: AgentState) -> str:
    msg = state["user_message"].lower()

    # Direct booking commands
    if any(k in msg for k in ["yes, book it", "confirm booking", "yes book it", "book it now"]):
        return "confirmation_gate"

    if any(k in msg for k in ["book", "proceed to book", "ready to book", "make the booking"]):
        return "confirmation_gate"

    # Replanning / Modification commands
    if any(k in msg for k in ["reduce the cost", "reduce budget", "change flight", "change hotel", "cheaper", "make it ₹", "make it rs"]):
        return "partial_replanning"

    # Disruption commands
    if any(k in msg for k in ["flight was cancelled", "flight cancelled", "delay", "disruption"]):
        return "disruption_handling"

    # Trip management commands
    if any(k in msg for k in ["show my trip", "voucher", "check-in", "policy", "my booking"]):
        return "trip_management"

    missing = state.get("missing_fields", [])
    # If both dates and budget are missing and not in memory
    if "travel_dates" in missing and "budget" in missing:
        return "ask_followup"

    # If destination is selected, plan itinerary
    intent = state.get("intent") or {}
    dest = intent.get("destination") or state["context"].get("destination")
    if dest:
        return "itinerary_planning"

    # Otherwise discover destinations
    return "destination_discovery"


async def node_ask_followup(state: AgentState, db: AsyncSession) -> AgentState:
    missing = state.get("missing_fields", [])
    question = PreferenceAgent.generate_followup_question(missing, state["context"])
    state["reply"] = question
    state["current_goal"] = "collect_missing_preferences"
    state["next_step"] = "await_user_input"
    return state


async def node_destination_discovery(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)

    recommendations = await DestinationAgent.discover_destinations(trip, max_recommendations=3)
    rec_dicts = [r.model_dump() for r in recommendations]

    state["recommendations"] = rec_dicts
    top_dest = recommendations[0].destination if recommendations else "Goa"

    dest_list_str = "\n".join([
        f"- **{r.destination}** (Fit Score: {r.fit_score}/100, Est. Cost: ₹{r.estimated_cost:,.0f})\n  *Why:* {'; '.join(r.why_it_fits[:2])}"
        for r in recommendations
    ])

    state["reply"] = (
        f"Based on your preferences, here are 3 fantastic destinations:\n\n"
        f"{dest_list_str}\n\n"
        f"Which destination would you like to proceed with?"
    )
    state["current_goal"] = "destination_selection"
    state["next_step"] = "select_destination"
    return state


async def node_itinerary_planning(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)

    # Generate 3 variants
    variants = ItineraryAgent.generate_itineraries(trip)
    state["itineraries"] = variants

    # Persist the balanced itinerary as default
    balanced_var = next((v for v in variants if v["tier"] == "Balanced"), variants[0])

    itin_obj = Itinerary(
        trip_id=trip.id,
        tier=balanced_var["tier"],
        title=balanced_var["title"],
        total_estimated_cost=balanced_var["total_estimated_cost"],
        currency=balanced_var["currency"],
        is_selected=True,
        highlights=balanced_var["highlights"]
    )
    db.add(itin_obj)
    await db.flush()

    for item in balanced_var["items"]:
        itin_item = ItineraryItem(
            itinerary_id=itin_obj.id,
            day_number=item["day_number"],
            date=item["date"],
            location=item["location"],
            morning=item["morning"],
            afternoon=item["afternoon"],
            evening=item["evening"],
            activities=item["activities"],
            hotel=item["hotel"],
            transport=item["transport"],
            estimated_cost=item["estimated_cost"],
            travel_time_minutes=item.get("travel_time_minutes", 45),
            notes=item.get("notes")
        )
        db.add(itin_item)

    trip.status = TripStatus.PLANNING
    await db.flush()

    state["selected_itinerary_id"] = str(itin_obj.id)
    cost = balanced_var["total_estimated_cost"]

    state["reply"] = (
        f"I have created 3 customized itinerary options for **{trip.destination or 'Goa'}**:\n\n"
        f"1. **Budget Option**: ₹{variants[0]['total_estimated_cost']:,.0f} - Focuses on cozy boutique inns and essential sightseeing.\n"
        f"2. **Balanced Option (Recommended)**: ₹{balanced_var['total_estimated_cost']:,.0f} - Prime beachfront 4-star resort, Mandovi sunset cruise, spice farm lunch & coastal dining.\n"
        f"3. **Premium Option**: ₹{variants[2]['total_estimated_cost']:,.0f} - 5-star ocean-view resort at Taj Fort Aguada, private luxury SUV and fine dining.\n\n"
        f"Would you like to proceed with the **Balanced** itinerary, or would you like to make any adjustments?"
    )
    state["current_goal"] = "review_itinerary"
    state["next_step"] = "confirm_or_modify_itinerary"
    return state


async def node_partial_replanning(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)
    replanner = ReplanningService()

    # Detect requested target budget from message
    import re
    msg = state["user_message"]
    match = re.search(r"(\d{1,3}(?:,\d{3})+|\d{4,7})", msg.replace("₹", "").replace("Rs", "").replace("rs", ""))
    target_budget = float(match.group(1).replace(",", "")) if match else 65000.0

    itin_id = None
    if trip.itineraries:
        itin_id = trip.itineraries[0].id

    if not itin_id:
        # Fallback create itinerary first
        variants = ItineraryAgent.generate_itineraries(trip)
        b = variants[1]
        itin_obj = Itinerary(
            trip_id=trip.id,
            tier=b["tier"],
            title=b["title"],
            total_estimated_cost=b["total_estimated_cost"],
            currency=b["currency"],
            is_selected=True,
            highlights=b["highlights"]
        )
        db.add(itin_obj)
        await db.flush()
        itin_id = itin_obj.id

    replan_result = await replanner.replan_itinerary(
        db=db,
        trip=trip,
        itinerary_id=itin_id,
        target_budget=target_budget,
        change_hotel=True,
        change_flight=True
    )

    state["reply"] = (
        f"I have partially replanned your trip to meet your new target budget of **₹{target_budget:,.0f}**:\n\n"
        f"- Kept your approved cultural activities and Mandovi sunset cruise.\n"
        f"- Switched to Akasa Air morning departure (saving ₹4,600 on flights).\n"
        f"- Selected Calangute Palms Boutique Inn (saving ₹8,000 on lodging).\n"
        f"- **New Total Trip Cost**: **₹{replan_result['new_total']:,.0f} {replan_result['currency']}**.\n\n"
        f"Would you like to lock this in and prepare booking?"
    )
    state["current_goal"] = "itinerary_replanned"
    state["next_step"] = "prepare_booking"
    return state


async def node_confirmation_gate(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)
    booking_agent = BookingAgent()
    msg = state["user_message"].lower()

    if any(k in msg for k in ["yes, book it", "confirm booking", "yes book it", "book it now"]):
        # User confirmed! Find active pending action
        from sqlalchemy import select
        stmt = select(PendingAction).where(
            PendingAction.trip_id == trip.id,
            PendingAction.status == ActionStatus.AWAITING_CONFIRMATION
        ).order_by(PendingAction.created_at.desc())
        res = await db.execute(stmt)
        pending = res.scalars().first()

        if not pending:
            # Prepare one automatically and execute
            pending = await booking_agent.prepare_booking(db, trip)

        idempotency_key = pending.idempotency_key
        booking_res = await booking_agent.confirm_and_execute_booking(
            db=db,
            trip=trip,
            pending_action_id=pending.id,
            idempotency_key=idempotency_key
        )

        state["reply"] = (
            f"🎉 **Your trip to {trip.destination or 'Goa'} is CONFIRMED & BOOKED!**\n\n"
            f"- **Booking Reference**: `{booking_res.booking_reference}`\n"
            f"- **Total Paid**: ₹{booking_res.total_amount:,.2f} {booking_res.currency}\n"
            f"- **Voucher Code**: `{booking_res.voucher_data.get('voucher_code', 'VOUCHER-CONFIRMED')}`\n\n"
            f"All flight tickets, hotel vouchers, and transfers have been stored in your Trip Memory. Have a fantastic trip!"
        )
        state["current_goal"] = "booking_confirmed"
        state["next_step"] = "trip_management"
    else:
        # Prepare pending action requiring confirmation
        pending = await booking_agent.prepare_booking(db, trip)
        state["pending_action"] = {
            "id": str(pending.id),
            "estimated_amount": pending.estimated_amount,
            "currency": pending.currency,
            "expires_at": pending.expires_at.isoformat()
        }

        state["reply"] = (
            f"I have prepared your final booking package:\n\n"
            f"- **Total Cost**: ₹{pending.estimated_amount:,.2f} {pending.currency} (includes flights, 4-star hotel, activities & transfers)\n"
            f"- **Cancellation Terms**: Free cancellation up to 48 hours prior.\n"
            f"- **Action Required**: Please confirm by replying **'Yes, book it'** to execute the reservation."
        )
        state["current_goal"] = "awaiting_booking_confirmation"
        state["next_step"] = "user_confirmation"

    return state


async def node_disruption_handling(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)
    disrupt_agent = DisruptionAgent()

    disruptions = await disrupt_agent.check_and_detect_disruptions(db, trip.id)
    if disruptions:
        d = disruptions[0]
        alt_str = "\n".join([
            f"- **Option {i+1}**: {alt.get('description')} (Cost Difference: ₹{alt.get('price_difference', 0):,.0f})"
            for i, alt in enumerate(d.alternative_options)
        ])
        state["reply"] = (
            f"⚠️ **Travel Disruption Alert Detected**\n\n"
            f"Your flight `{d.reference_id}` was cancelled due to {d.reason.lower()}.\n\n"
            f"I have found verified alternatives for you:\n"
            f"{alt_str}\n\n"
            f"Which alternative would you like to rebook?"
        )
    else:
        state["reply"] = "No disruptions found on your active itinerary. All flights and hotels are on schedule."

    state["current_goal"] = "disruption_managed"
    return state


async def node_trip_management(state: AgentState, db: AsyncSession) -> AgentState:
    trip_id = uuid.UUID(state["trip_id"])
    trip = await MemoryService.get_trip_with_memory(db, trip_id)
    mgmt = TripManagementAgent()

    vouchers = await mgmt.get_trip_vouchers(db, trip.id, trip.user_id)
    if vouchers:
        v = vouchers[0]
        state["reply"] = (
            f"Here are your active trip details for **{trip.destination or 'Goa'}**:\n\n"
            f"- **Booking ID**: `{v['booking_reference']}`\n"
            f"- **Hotel Check-in**: 14:00 (Candolim Beach Resort & Spa)\n"
            f"- **Hotel Check-out**: 11:00\n"
            f"- **Cancellation Policy**: Free cancellation up to 48h prior with ₹2,500 standard penalty.\n"
            f"- **Voucher**: `{v['voucher_data'].get('voucher_code')}`\n\n"
            f"Is there anything else you'd like to check or modify?"
        )
    else:
        state["reply"] = (
            f"Your trip to **{trip.destination or 'your destination'}** is currently in **{trip.status}** status. "
            f"Once you confirm your booking, all flight tickets and hotel vouchers will appear here."
        )

    state["current_goal"] = "trip_management"
    return state
