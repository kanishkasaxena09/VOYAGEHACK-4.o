from typing import Any, Dict, List, Optional
from app.agents.orchestrator import llm_client
from app.models.trip import Trip
from app.schemas.destination import DestinationRecommendationResponse


class DestinationAgent:
    CATALOG = [
        {
            "destination": "Goa",
            "base_fit_score": 92,
            "interests": ["beaches", "food", "relaxed", "sightseeing", "nightlife"],
            "why_it_fits": [
                "Beach-focused with relaxed atmosphere",
                "World-renowned Goan seafood and coastal cuisine",
                "Suitable for a relaxed 5-day getaway for couples or friends",
                "Wide variety of comfortable boutique resorts within budget"
            ],
            "tradeoffs": [
                "Peak season tourist rush around North Goa beaches in December",
                "Local cab fares can be relatively high without scooters"
            ],
            "weather_info": "Pleasant tropical weather in December (22°C - 31°C) with dry sunny skies.",
            "estimated_cost_per_couple": 65000.0,
            "currency": "INR"
        },
        {
            "destination": "Kerala",
            "base_fit_score": 88,
            "interests": ["beaches", "nature", "relaxed", "food", "culture"],
            "why_it_fits": [
                "Scenic backwaters and tranquil Marari & Varkala beaches",
                "Authentic South Indian culinary experiences",
                "Relaxed pace with Ayurvedic wellness options",
                "Easily managed within a moderate budget"
            ],
            "tradeoffs": [
                "Travel times between Cochin, Alleppey and beaches require 1-2 hour car transfers",
                "Nightlife is quieter compared to Goa"
            ],
            "weather_info": "Mild coastal warmth in December (23°C - 30°C) with low humidity.",
            "estimated_cost_per_couple": 72000.0,
            "currency": "INR"
        },
        {
            "destination": "Andaman",
            "base_fit_score": 84,
            "interests": ["beaches", "adventure", "nature", "relaxed"],
            "why_it_fits": [
                "Pristine turquoise waters at Radhanagar & Elephant beaches",
                "World-class marine biodiversity and coral reefs",
                "Uncrowded, serene island environment ideal for relaxation"
            ],
            "tradeoffs": [
                "Flight costs from mainland cities can be higher",
                "Requires inter-island ferry scheduling"
            ],
            "weather_info": "Balmy island breeze (24°C - 29°C) with clear waters perfect for swimming.",
            "estimated_cost_per_couple": 78000.0,
            "currency": "INR"
        },
        {
            "destination": "Jaipur",
            "base_fit_score": 75,
            "interests": ["heritage", "culture", "sightseeing", "food"],
            "why_it_fits": [
                "Magnificent royal palaces and UNESCO World Heritage forts",
                "Rich Rajasthani dining and vibrant bazaar shopping",
                "Excellent road/rail connectivity from Delhi"
            ],
            "tradeoffs": [
                "No beaches (cultural/heritage destination)",
                "Pace can be more active and busy than a beach retreat"
            ],
            "weather_info": "Crisp winter weather (10°C - 24°C) with cool evenings.",
            "estimated_cost_per_couple": 48000.0,
            "currency": "INR"
        }
    ]

    @classmethod
    async def discover_destinations(
        cls,
        trip: Trip,
        max_recommendations: int = 3
    ) -> List[DestinationRecommendationResponse]:
        user_interests = set(i.lower() for i in trip.interests)
        user_budget = trip.budget_amount or 80000.0
        recommendations = []

        for item in cls.CATALOG:
            # Score calculation
            score = item["base_fit_score"]
            dest_interests = set(item["interests"])

            # Interest match boost
            matches = len(user_interests.intersection(dest_interests))
            score += matches * 3

            # Budget penalty if estimated cost exceeds user budget
            est_cost = item["estimated_cost_per_couple"]
            if est_cost > user_budget:
                excess_ratio = (est_cost - user_budget) / user_budget
                score -= int(excess_ratio * 30)

            # Cap score 0-99
            score = max(50, min(98, score))

            rec = DestinationRecommendationResponse(
                destination=item["destination"],
                fit_score=score,
                why_it_fits=item["why_it_fits"],
                tradeoffs=item["tradeoffs"],
                estimated_cost=est_cost,
                currency=item["currency"],
                weather_info=item["weather_info"],
                is_selected=bool(trip.destination and trip.destination.lower() == item["destination"].lower())
            )
            recommendations.append(rec)

        # Sort by fit_score descending
        recommendations.sort(key=lambda x: x.fit_score, reverse=True)
        return recommendations[:max_recommendations]
