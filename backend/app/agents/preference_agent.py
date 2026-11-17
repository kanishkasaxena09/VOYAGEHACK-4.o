import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from app.agents.orchestrator import llm_client
from app.core.logging import logger
from app.models.trip import Trip
from app.schemas.trip import TravelIntent


class PreferenceAgent:
    SYSTEM_PROMPT = """You are a specialized Travel Preference & Constraint Extraction Agent.
Your job is to analyze the user's travel request and extract all structured preferences, hard constraints, and soft preferences.
Hard constraints are non-negotiable (e.g. max budget, strict non-stop flight, exact dates).
Soft preferences are flexible (e.g. likes beach, relaxed pace, nice food).
Do not fabricate facts. If information is not provided by the user, leave it null."""

    @classmethod
    async def extract_preferences(
        cls,
        user_message: str,
        existing_trip: Optional[Trip] = None
    ) -> TravelIntent:
        """Extract structured intent using LLM if available, with deterministic NLP fallback."""
        print("PreferenceAgent.extract_preferences called with:", user_message)
        user_prompt = f"User Request: \"{user_message}\""
        if existing_trip:
            user_prompt += (
                f"\nExisting Trip Memory:"
                f"\n- Origin: {existing_trip.origin}"
                f"\n- Destination: {existing_trip.destination}"
                f"\n- Dates: {existing_trip.start_date} to {existing_trip.end_date}"
                f"\n- Duration: {existing_trip.duration_days} days"
                f"\n- Travellers: {existing_trip.number_of_travellers}"
                f"\n- Budget: {existing_trip.budget_currency} {existing_trip.budget_amount}"
                f"\n- Interests: {', '.join(existing_trip.interests)}"
            )

        # 1. Try structured LLM call first
        if llm_client.is_available:
            print("LLM is available, calling Groq...")
            structured_res = await llm_client.generate_structured(
                system_prompt=cls.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=TravelIntent
            )
            if structured_res:
                cls._post_process_missing(structured_res, existing_trip)
                return structured_res

        # 2. Deterministic NLP extraction fallback
        print("Calling _deterministic_extract...")
        return cls._deterministic_extract(user_message, existing_trip)

    @classmethod
    def _deterministic_extract(
        cls,
        text: str,
        existing_trip: Optional[Trip] = None
    ) -> TravelIntent:
        t = text.lower()
        intent = TravelIntent()

        # Destination detection
        destinations = ["goa", "kerala", "andaman", "jaipur", "manali", "kashmir", "delhi", "mumbai", "bali", "thailand"]
        for dest in destinations:
            if re.search(r"\b" + re.escape(dest) + r"\b", t):
                intent.destination = dest.capitalize()
                break

        # Duration detection (e.g. "5-day", "5 days")
        dur_match = re.search(r"\b(\d+)\s*-\s*day|\b(\d+)\s+days?\b", t)
        if dur_match:
            d_str = dur_match.group(1) or dur_match.group(2)
            intent.duration_days = int(d_str)

        # Travellers detection
        trav_match = re.search(r"\b(\d+)\s+(?:people|persons|travellers|travelers|adults)\b", t)
        if trav_match:
            intent.number_of_travellers = int(trav_match.group(1))
        elif "two people" in t or "for 2" in t or "couple" in t or "for two" in t:
            intent.number_of_travellers = 2
        elif "solo" in t or "for myself" in t or "1 person" in t:
            intent.number_of_travellers = 1

        # Budget detection (clean, non-backtracking)
        b_direct = re.search(r"(?:budget|cost)\s*(?:is|of|around)?\s*[:=]?\s*[₹rs\.inr\s]*(\d+[\d,]*)", t)
        if b_direct:
            raw_b = b_direct.group(1).replace(",", "")
            try:
                intent.budget = float(raw_b)
                intent.currency = "INR"
                intent.hard_constraints.append(f"MAX_BUDGET={intent.budget}")
            except ValueError:
                pass
        else:
            sym_match = re.search(r"[₹]\s*(\d+[\d,]*)", t)
            if sym_match:
                try:
                    intent.budget = float(sym_match.group(1).replace(",", ""))
                    intent.currency = "INR"
                    intent.hard_constraints.append(f"MAX_BUDGET={intent.budget}")
                except ValueError:
                    pass

        # Interests detection
        interests_list = ["beach", "beaches", "food", "sightseeing", "relaxed", "adventure", "culture", "nature", "nightlife", "heritage"]
        for interest in interests_list:
            if interest in t:
                clean_int = "beaches" if interest == "beach" else interest
                if clean_int not in intent.interests:
                    intent.interests.append(clean_int)

        # Dates detection
        if "december 10" in t or "10-14" in t or "10 to 14" in t:
            intent.start_date = date(2026, 12, 10)
            intent.end_date = date(2026, 12, 14)
            intent.duration_days = 5
        elif "december" in t:
            intent.soft_preferences.append("Travel in December")

        # Hotel / flight preferences
        if "don't want expensive hotels" in t or "budget hotel" in t or "reasonable hotel" in t:
            intent.hotel_preference = "Budget to 3-Star"
            intent.soft_preferences.append("Avoid luxury expensive hotels")

        if "relaxed" in t:
            intent.pace = "relaxed"
            intent.soft_preferences.append("Relaxed travel pace")

        cls._post_process_missing(intent, existing_trip)
        return intent

    @classmethod
    def _post_process_missing(
        cls,
        intent: TravelIntent,
        existing_trip: Optional[Trip] = None
    ) -> None:
        missing = []

        dest = intent.destination or (existing_trip.destination if existing_trip else None)
        if not dest:
            missing.append("destination")

        dates_known = (
            (intent.start_date and intent.end_date)
            or (existing_trip and existing_trip.start_date and existing_trip.end_date)
            or (intent.duration_days or (existing_trip and existing_trip.duration_days))
        )
        if not dates_known:
            missing.append("travel_dates")

        budget_known = intent.budget or (existing_trip and existing_trip.budget_amount)
        if not budget_known:
            missing.append("budget")

        intent.missing_fields = missing

    @classmethod
    def generate_followup_question(
        cls,
        missing_fields: List[str],
        known_context: Dict[str, Any]
    ) -> str:
        if not missing_fields:
            return "Thank you! I have all your core travel requirements. Let me find the best options for you."

        if "travel_dates" in missing_fields and "budget" in missing_fields:
            return "What dates in December are you considering, and what is your approximate budget?"
        elif "travel_dates" in missing_fields:
            return "What specific travel dates or duration would you prefer?"
        elif "budget" in missing_fields:
            return "What is your approximate budget for this trip?"
        elif "destination" in missing_fields:
            return "Do you have a specific destination in mind, or would you like me to recommend top beach and cultural spots?"
        else:
            return f"Could you provide a few more details regarding: {', '.join(missing_fields)}?"
