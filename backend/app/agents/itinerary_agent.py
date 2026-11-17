from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from app.models.trip import Trip


class ItineraryAgent:
    @classmethod
    def generate_itineraries(
        cls,
        trip: Trip,
        destination: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        dest = destination or trip.destination or "Goa"
        duration = trip.duration_days or 5
        start_d = trip.start_date or date(2026, 12, 10)
        travellers = trip.number_of_travellers or 2

        itineraries = []

        # 1. Budget Itinerary
        budget_itinerary = cls._build_variant(
            tier="Budget",
            title=f"5-Day Smart Budget {dest} Getaway",
            dest=dest,
            duration=duration,
            start_date=start_d,
            hotel_name="Calangute Palms Boutique Inn",
            hotel_nightly=3200.0,
            flight_price=11200.0,
            transfer_price=3800.0,
            activity_mult=0.7,
            travellers=travellers,
            highlights=[
                "Affordable beachside boutique lodging walking distance from coast",
                "Self-paced beach sunset strolls and authentic Goan beach shacks",
                "Spice plantation cultural tour with traditional lunch included"
            ]
        )
        itineraries.append(budget_itinerary)

        # 2. Balanced Itinerary
        balanced_itinerary = cls._build_variant(
            tier="Balanced",
            title=f"5-Day Relaxed Beach & Culture {dest} Retreat",
            dest=dest,
            duration=duration,
            start_date=start_d,
            hotel_name="Candolim Beach Resort & Spa",
            hotel_nightly=5200.0,
            flight_price=13500.0,
            transfer_price=3800.0,
            activity_mult=1.0,
            travellers=travellers,
            highlights=[
                "Prime beachfront 4-star resort with swimming pool & spa access",
                "Mandovi river sunset cultural cruise with Goan folk music",
                "UNESCO heritage churches in Old Goa & Spice Farm buffet",
                "Curated Anjuna cliff sunset dinner & seafood tastings"
            ]
        )
        itineraries.append(balanced_itinerary)

        # 3. Premium Itinerary
        premium_itinerary = cls._build_variant(
            tier="Premium",
            title=f"5-Day Luxury Heritage & Ocean View {dest} Experience",
            dest=dest,
            duration=duration,
            start_date=start_d,
            hotel_name="Taj Fort Aguada Resort & Spa",
            hotel_nightly=14500.0,
            flight_price=14200.0,
            transfer_price=5500.0,
            activity_mult=1.5,
            travellers=travellers,
            highlights=[
                "Historic 5-star beachfront luxury at Taj Fort Aguada with private sea views",
                "Private chauffeured luxury SUV throughout the trip",
                "Private sunset yacht charter and exclusive beach fine-dining",
                "Dedicated concierge & personalized Ayurvedic spa therapy"
            ]
        )
        itineraries.append(premium_itinerary)

        return itineraries

    @classmethod
    def _build_variant(
        cls,
        tier: str,
        title: str,
        dest: str,
        duration: int,
        start_date: date,
        hotel_name: str,
        hotel_nightly: float,
        flight_price: float,
        transfer_price: float,
        activity_mult: float,
        travellers: int,
        highlights: List[str]
    ) -> Dict[str, Any]:
        days_data = []
        hotel_total = hotel_nightly * (duration - 1)
        total_flight = flight_price * travellers
        total_transfer = transfer_price

        total_activity_cost = 0.0

        for day_num in range(1, duration + 1):
            curr_date = start_date + timedelta(days=day_num - 1)
            date_str = curr_date.isoformat()

            if day_num == 1:
                morning = f"Morning arrival at {dest} Airport. Meet private chauffeur at arrival hall."
                afternoon = f"Check-in at {hotel_name}. Unpack, freshen up, and enjoy welcome drinks."
                evening = "Leisure stroll along the beach to watch the sunset followed by dinner at a beachfront cafe."
                acts = [{"id": f"ACT-{dest[:3]}-ARR", "title": "Airport Transfer & Hotel Check-in", "price": 0.0}]
                trans = {"mode": "Private Transfer", "total_price": total_transfer, "route": f"Airport to {hotel_name}"}
                day_cost = total_transfer + (total_flight if day_num == 1 else 0.0) + (hotel_total / (duration - 1))
            elif day_num == 2:
                morning = "Relaxed poolside breakfast. Head to Old Goa historical quarter."
                afternoon = "Guided walk through Basilica of Bom Jesus and Se Cathedral, followed by authentic Goan lunch."
                evening = "Mandovi River sunset cruise with Goan cultural dance and live music."
                act_cost = round(1200.0 * activity_mult * travellers, 2)
                total_activity_cost += act_cost
                acts = [{"id": f"ACT-{dest[:3]}-2", "title": "Mandovi River Sunset Cruise", "price": act_cost}]
                trans = {"mode": "Air-Conditioned Cab", "total_price": 0.0}
                day_cost = act_cost
            elif day_num == 3:
                morning = "Visit Sahakari Spice Plantation. Enjoy traditional welcoming garland and herbal tea."
                afternoon = "Plantation walk exploring cardamom, peri-peri, and vanilla. Sumptuous traditional Goan buffet lunch."
                evening = "Relax on the beach with fresh coconut water and sunset sea views."
                act_cost = round(2200.0 * activity_mult * travellers, 2)
                total_activity_cost += act_cost
                acts = [{"id": f"ACT-{dest[:3]}-3", "title": "Spice Plantation & Heritage Tour", "price": act_cost}]
                trans = {"mode": "Air-Conditioned Cab", "total_price": 0.0}
                day_cost = act_cost
            elif day_num == 4:
                morning = "Free morning for sleep-in or swimming. Late brunch."
                afternoon = "Explore vibrant local flea markets and beach boutiques in Anjuna and Vagator."
                evening = "Sunset seafood tasting at cliffside open-air lounge overlooking the Arabian Sea."
                act_cost = round(1500.0 * activity_mult * travellers, 2)
                total_activity_cost += act_cost
                acts = [{"id": f"ACT-{dest[:3]}-4", "title": "Anjuna Sunset Beach Walk & Seafood Tasting", "price": act_cost}]
                trans = {"mode": "Air-Conditioned Cab", "total_price": 0.0}
                day_cost = act_cost
            else:
                morning = "Lazy breakfast at the resort. Final swim and packing."
                afternoon = f"11:00 AM check-out from {hotel_name}. Souvenir shopping."
                evening = "Chauffeured transfer to the airport for return evening flight."
                acts = [{"id": f"ACT-{dest[:3]}-DEP", "title": "Hotel Check-out & Departure Transfer", "price": 0.0}]
                trans = {"mode": "Return Airport Transfer", "total_price": 0.0}
                day_cost = 0.0

            days_data.append({
                "day_number": day_num,
                "date": curr_date,
                "location": dest,
                "morning": morning,
                "afternoon": afternoon,
                "evening": evening,
                "activities": acts,
                "hotel": {
                    "name": hotel_name,
                    "price_per_night": hotel_nightly,
                    "total_price": hotel_total
                },
                "transport": trans,
                "estimated_cost": round(day_cost, 2),
                "travel_time_minutes": 45,
                "notes": "Pace is deliberately kept relaxed to avoid rushing."
            })

        total_est = round(total_flight + hotel_total + total_activity_cost + total_transfer, 2)

        return {
            "tier": tier,
            "title": title,
            "total_estimated_cost": total_est,
            "currency": "INR",
            "highlights": highlights,
            "items": days_data
        }
