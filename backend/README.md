# Intelligent Virtual Travel Agent — Production Backend

A production-grade agentic Python backend built for an Intelligent Virtual Travel Agent. This backend manages the entire travel lifecycle end-to-end:

**Inspiration → Preference Collection → Destination Discovery → Itinerary Planning → Live/Mock Search → Price Comparison → User Confirmation → Booking → Trip Management → Cancellation/Modification → Disruption Handling**

Unlike standard conversational chatbots, this system is a **state-driven, multi-agent AI system** built with **LangGraph**, **FastAPI**, **SQLAlchemy 2.x (async)**, and **Pydantic v2**. It enforces **strict separation between probabilistic AI reasoning and deterministic business logic**:

1. **LLM Is Never the Source of Truth**: The LLM never invents flight/hotel prices, availability, booking IDs, confirmation numbers, or refund sums. All pricing and availability originate from certified travel providers.
2. **Two-Step Human Confirmation Gates**: High-consequence operations (booking execution, flight/hotel cancellations, paid itinerary changes, and disruption resolutions) require explicit user confirmation through an idempotent, expiring `PendingAction` state machine.
3. **Deterministic Total Cost Engine**: Backend-calculated pricing with explicit item breakdown, taxes, provider fees, and currency consistency.
4. **Dependency-Aware Partial Replanning**: When one component changes (e.g., flight modified or budget adjusted), approved hotels and activities are preserved rather than recomputing the entire trip from scratch.
5. **Persistent Trip Memory**: Complete relational state stored in PostgreSQL/SQLite tracking travellers, preferences, hard constraints, conversation turns, destination options, multi-tier itineraries, search caches, bookings, audit logs, and disruptions.

---

## 1. High-Level Architecture

```text
 Client / Frontend
        |
        v
 FastAPI REST API (JWT Auth + RBAC + Idempotency)
        |
        v
 LangGraph Orchestrator (Stateful Multi-Agent Workflow)
        |
        +-----------------------------------------------+
        |                                               |
        v                                               v
 Trip Memory Service                             Tool Registry
 (PostgreSQL / SQLite via SQLAlchemy 2.0 Async)  (Mock & Real Provider Abstraction)
        |                                               |
        +-- Users & Travellers                          +-- FlightProvider
        +-- Trips & Preferences                         +-- HotelProvider
        +-- Hard & Soft Constraints                     +-- ActivityProvider
        +-- Multi-Tier Itineraries                      +-- TransferProvider
        +-- Confirmed Bookings                          +-- BookingProvider
        +-- PendingAction State Machine                 +-- DisruptionMonitor
        +-- Audit Log Trail
```

---

## 2. Specialized Multi-Agent Network

| Agent Module | Primary Responsibility |
|---|---|
| **Preference & Constraint Agent** (`preference_agent.py`) | Extracts dates, budget, origin, destination, party size, travel pace, and diet. Distinguishes hard constraints (budget ceilings, non-stop flights) from soft preferences. Detects missing fields and generates focused follow-ups. |
| **Destination Discovery Agent** (`destination_agent.py`) | Scores destinations (0–99 fit score) based on season, interests, budget feasibility, and travel style. Generates structured fit justifications and tradeoffs. |
| **Itinerary Planner Agent** (`itinerary_agent.py`) | Generates 3 full itinerary tiers: **Budget**, **Balanced**, and **Premium**. Formulates day-by-day morning/afternoon/evening schedules, travel durations, and curated activities. |
| **Search & Pricing Agent** (`search_agent.py`) | Interfaces with provider abstractions (`FlightProvider`, `HotelProvider`, etc.). Normalizes search results, checks availability, and validates freshness. |
| **Booking Agent** (`booking_agent.py`) | Prepares quotes, creates expiring `PendingAction` records, verifies idempotency keys, and triggers provider reservation flows. Generates vouchers and booking references. |
| **Trip Management Agent** (`trip_management_agent.py`) | Executes partial replanning without destroying approved segments. Handles cancellation and modification policies with deterministic refund and penalty calculations. |
| **Disruption Agent** (`disruption_agent.py`) | Monitors travel status for delays and cancellations. Automatically computes rerouting options and alternative itineraries with exact price diffs, presenting solutions for user approval. |

---

## 3. Technology Stack

- **Python**: 3.12+
- **Web Framework**: FastAPI, Starlette, Uvicorn (ASGI)
- **Validation**: Pydantic v2 (ConfigDict, model validation)
- **Database ORM**: SQLAlchemy 2.0 (Fully Async with `asyncpg` for PostgreSQL and `aiosqlite` for SQLite testing)
- **Migrations**: Alembic
- **Agent Orchestration**: LangGraph, LangChain Core
- **LLM Engine**: Groq LLM API (`llama-3.3-70b-versatile`) with offline fallback
- **Authentication**: JWT (JSON Web Tokens) with `bcrypt` / `passlib`
- **Testing**: `pytest`, `pytest-asyncio`, `httpx`
- **Execution**: Direct Uvicorn ASGI server with one-command runner (`python run.py`)

---

## 4. Project Directory Structure

```text
backend/
├── run.py                        # Simple one-command application launcher
├── start.bat                     # Windows batch launcher (double-click to start)
├── alembic.ini                   # Alembic database migration configuration
├── pytest.ini                    # Pytest settings and asyncio test mode
├── requirements.txt              # Python package requirements
├── .env.example                  # Environment template
│
├── mock_data/                    # Provider seed data
│   ├── flights.json              # Realistic domestic & international flights
│   ├── hotels.json               # Hotels with categories, policies, and nightly rates
│   ├── activities.json           # Sightseeing, water sports, dining, and culture
│   ├── transfers.json            # Airport transfers and private cabs
│   └── disruptions.json          # Weather, mechanical, and delay disruption events
│
├── app/
│   ├── main.py                   # FastAPI application initialization & middleware
│   │
│   ├── core/                     # Application foundation
│   │   ├── config.py             # Pydantic BaseSettings & .env management
│   │   ├── security.py           # Password hashing & JWT token issue/decode
│   │   ├── exceptions.py         # Standardized domain error classes
│   │   └── logging.py            # Structured system logger
│   │
│   ├── db/                       # Database engine and migrations
│   │   ├── database.py           # Async engine, sessionmaker, and multi-dialect GUID
│   │   └── migrations/           # Alembic revision scripts
│   │
│   ├── models/                   # SQLAlchemy 2.0 ORM Entities
│   │   ├── user.py               # User accounts & auth
│   │   ├── trip.py               # Central Trip aggregate root
│   │   ├── traveller.py          # Party members & passenger details
│   │   ├── preference.py         # Preferences & Hard/Soft constraints
│   │   ├── conversation.py       # Chat conversations & message audit
│   │   ├── destination.py        # Destination fit recommendations
│   │   ├── itinerary.py          # Multi-tier itineraries & day items
│   │   ├── search.py             # Search cache & price quotes
│   │   ├── booking.py            # Confirmed bookings & vouchers
│   │   ├── pending_action.py     # Two-step confirmation state machine
│   │   ├── disruption.py         # Flight/Hotel disruption tracking
│   │   ├── audit.py              # Security & operational audit logs
│   │   └── notification.py       # Notification queue
│   │
│   ├── schemas/                  # Pydantic v2 Request/Response DTOs
│   │   ├── auth.py               # User register, login, and tokens
│   │   ├── common.py             # Standardized APIResponse[T] envelope
│   │   ├── trip.py               # Trip create/update, preferences, constraints
│   │   ├── chat.py               # Chat input & stateful agent responses
│   │   ├── destination.py        # Recommendations & discovery requests
│   │   ├── itinerary.py          # Day items, tiers, and replanning DTOs
│   │   ├── search.py             # Flight/hotel/activity search requests & responses
│   │   ├── pricing.py            # Deterministic cost breakdowns
│   │   ├── booking.py            # PendingAction & Booking confirmation schemas
│   │   └── disruption.py         # Disruption alert & resolution schemas
│   │
│   ├── providers/                # Provider abstraction layer
│   │   ├── base.py               # Abstract Base Classes (ABC)
│   │   ├── mock_flights.py       # FlightProvider implementation
│   │   ├── mock_hotels.py        # HotelProvider implementation
│   │   ├── mock_activities.py    # ActivityProvider implementation
│   │   ├── mock_transfers.py     # TransferProvider implementation
│   │   └── mock_booking.py       # BookingProvider implementation
│   │
│   ├── services/                 # Business logic & domain services
│   │   ├── cost_service.py       # Deterministic Total Cost Engine
│   │   ├── pricing_service.py    # Price freshness & provider validation
│   │   ├── confirmation_service.py # PendingAction state machine & idempotency
│   │   ├── memory_service.py     # Trip memory persistence & history
│   │   ├── replanning_service.py # Dependency-aware partial replanner
│   │   ├── trip_service.py       # Trip CRUD & lifecycle status
│   │   └── audit_service.py      # Immutable audit trail logger
│   │
│   ├── agents/                   # Specialized AI Agents
│   │   ├── orchestrator.py       # Groq LLM client with timeout & offline fallback
│   │   ├── preference_agent.py   # Intent & constraint extraction
│   │   ├── destination_agent.py  # Destination discovery & fit scoring
│   │   ├── itinerary_agent.py    # Multi-tier itinerary builder
│   │   ├── search_agent.py       # Multi-service search agent
│   │   ├── booking_agent.py      # Reservation & voucher agent
│   │   ├── trip_management_agent.py # Cancellation & modification agent
│   │   └── disruption_agent.py   # Disruption detection & rerouting agent
│   │
│   ├── graph/                    # LangGraph orchestration
│   │   ├── state.py              # AgentState TypedDict definition
│   │   ├── nodes.py              # Orchestration node functions
│   │   └── graph.py              # StateGraph assembly & conditional routing
│   │
│   └── api/                      # REST API routing
│       ├── deps.py               # Database & JWT auth dependencies
│       └── routes/               # Modular router definitions
│           ├── auth.py           # Register, login, me
│           ├── trips.py          # Trips CRUD, preferences, constraints
│           ├── chat.py           # Agentic chat conversation endpoint
│           ├── destinations.py   # Destination discovery & selection
│           ├── itinerary.py      # Itinerary generation, selection & replanning
│           ├── search.py         # Live/mock travel search
│           ├── pricing.py        # Deterministic cost engine & validation
│           ├── bookings.py       # Prepare, confirm, cancel, and modify
│           └── disruptions.py    # Check disruptions and confirm resolutions
│
└── tests/                        # Comprehensive test suite (15 tests)
    ├── conftest.py               # Async fixtures, test client, and isolated test DB
    ├── test_agents.py            # Unit & LangGraph conversational flow tests
    ├── test_auth.py              # JWT authentication & registration tests
    ├── test_booking.py           # Booking, cancellation, and modification tests
    ├── test_pricing.py           # Deterministic cost engine & validation tests
    ├── test_replanning.py        # Dependency-aware partial replanning tests
    ├── test_safety.py            # Human confirmation gates & access control tests
    ├── test_search.py            # Multi-provider search integration tests
    └── test_trip.py              # Trip memory CRUD lifecycle tests
```

---

## 5. Quick Start

The backend is configured to run directly with local **SQLite** and realistic built-in travel providers out of the box with zero external infrastructure.

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Server (One Command)
```bash
python run.py
```
*(On Windows, you can also just double-click `start.bat`)*

That's it! The SQLite database tables are created automatically on startup.

### 3. Open Interactive Swagger API Docs
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Healthcheck**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

*(Optional: If you wish to use live Groq LLM inference, simply paste your key into `backend/.env` under `GROQ_API_KEY=`. If left blank, the backend runs in deterministic NLP fallback mode without needing any external API calls).*

---

## 6. Running the Test Suite

The test suite contains **15 automated tests** covering unit agent logic, LangGraph conversational flows, search and pricing engines, booking state machines, access security, and partial replanning:

```bash
python -m pytest backend/tests -v
```

### Test Coverage Highlights:
- `test_preference_agent_extraction`: Verifies regex and NLP intent extraction, date parsing, budget constraints, and missing-information identification.
- `test_destination_agent_recommendations`: Tests fit score ranking against budget and interest heuristics.
- `test_itinerary_agent_variants`: Validates generation of Budget, Balanced, and Premium tiers.
- `test_chat_endpoint_langgraph_flow`: Tests conversational multi-turn dialogue through the compiled LangGraph workflow.
- `test_register_and_login_flow`: Tests password hashing, JWT issue, and profile access.
- `test_complete_booking_cancellation_and_modification`: Tests the complete lifecycle: Quote Preparation → Two-step Confirmation → Booking Creation → Cancellation Policy Application → Refund Calculation.
- `test_deterministic_cost_engine_calculation`: Confirms mathematical accuracy of item subtotals, GST taxes, service charges, and discounts.
- `test_partial_replanning_flow`: Validates that changing flights preserves approved hotels and recalculates total pricing.
- `test_booking_cannot_happen_without_confirmation`: Enforces the security guarantee that bookings fail without an approved `PendingAction`.
- `test_user_a_cannot_access_user_b_trip`: Verifies multi-tenant isolation and 403 Forbidden enforcement.

---

## 7. Complete API Walkthrough & Lifecycle Demonstration

### Step 1: User Registration & Authentication

**Request**:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "traveler@example.com",
    "password": "SecurePassword123!",
    "full_name": "Rohan Sharma"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "76ec2fbe-c820-4ff6-9f7a-8b89d6e87f1a",
    "email": "traveler@example.com",
    "full_name": "Rohan Sharma",
    "is_active": true
  },
  "message": "User registered successfully"
}
```

Obtain JWT Token via `/api/auth/login`:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "traveler@example.com",
    "password": "SecurePassword123!"
  }'
```

---

### Step 2: Initialize Trip Memory

**Request**:
```bash
curl -X POST http://localhost:8000/api/trips \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Winter Beach Getaway"
  }'
```

---

### Step 3: Natural Language Conversational Planning (LangGraph)

User expresses their unstructured desire:
> *"I want a 5-day trip for 2 people in December. My budget is ₹80,000. I like beaches, food and relaxed sightseeing. I don't want expensive hotels."*

**Request**:
```bash
curl -X POST http://localhost:8000/api/trips/<TRIP_ID>/chat \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a 5-day trip for 2 people in December. My budget is ₹80,000. I like beaches, food and relaxed sightseeing. I don'\''t want expensive hotels."
  }'
```

**Agent Response**:
- Automatically extracts:
  - Duration: 5 days
  - Party: 2 travellers
  - Budget: ₹80,000 INR (Hard Constraint)
  - Hotel Category: Mid-range / Budget
  - Interests: Beach, Food, Sightseeing
  - Pace: Relaxed
- Identifies missing fields (e.g., origin city).
- Recommends top matching destinations (e.g., **Goa** [Fit Score: 94], **Andaman** [Fit Score: 88], **Kerala** [Fit Score: 86]).
- Updates conversational goal to `destination_selection`.

---

### Step 4: Generate Multi-Tier Itineraries

**Request**:
```bash
curl -X POST http://localhost:8000/api/trips/<TRIP_ID>/itinerary/generate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Goa",
    "tiers": ["Budget", "Balanced", "Premium"]
  }'
```

Produces 3 distinct itineraries:
1. **Budget Option**: Homestays / 3-star beach cottages, public/scooter transport, popular beach shacks (Estimated: ₹42,000).
2. **Balanced Option**: 4-star beach resort, private AC cab transfers, North & South Goa exploration, water sports (Estimated: ₹68,500).
3. **Premium Option**: 5-star beachfront luxury, private yacht sunset cruise, fine dining (Estimated: ₹95,000).

---

### Step 5: Partial Replanning (Change Component Without Redoing Trip)

User request: *"Keep the hotel and activities, but search for a cheaper flight."*

**Request**:
```bash
curl -X POST http://localhost:8000/api/trips/<TRIP_ID>/itinerary/replan \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "change_flight": true,
    "change_hotel": false,
    "change_activities": false,
    "explanation": "Switch to morning low-cost flight"
  }'
```

**Result**:
- Approved hotel reservation and scheduled activities remain untouched.
- Re-queries the `FlightProvider` for alternate options.
- Updates flight line item and re-runs `CostService` to calculate updated total.

---

### Step 6: Total Cost Calculation & Price Freshness Gate

**Request**:
```bash
curl -X GET http://localhost:8000/api/trips/<TRIP_ID>/pricing/total \
  -H "Authorization: Bearer <TOKEN>"
```

**Response**:
```json
{
  "success": true,
  "data": {
    "trip_id": "c1f7b029-...",
    "subtotal": 58000.0,
    "taxes_and_fees": 7250.0,
    "provider_breakdown": {
      "flights": 18000.0,
      "hotels": 28000.0,
      "activities": 8000.0,
      "transfers": 4000.0
    },
    "total_estimated_cost": 65250.0,
    "currency": "INR",
    "is_stale": false,
    "validated_at": "2026-11-17T10:00:00Z"
  }
}
```

---

### Step 7: Two-Step Booking Confirmation (Human-in-the-Loop)

#### Phase 1: Prepare Booking Quote (Creates Expiring PendingAction)

**Request**:
```bash
curl -X POST http://localhost:8000/api/trips/<TRIP_ID>/booking/prepare \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "user_checkout_attempt_001"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "action_998877",
    "action_type": "BOOKING_CONFIRMATION",
    "status": "AWAITING_CONFIRMATION",
    "estimated_amount": 65250.0,
    "currency": "INR",
    "expires_at": "2026-11-17T10:15:00Z",
    "idempotency_key": "user_checkout_attempt_001"
  },
  "message": "Quote prepared. Awaiting human confirmation within 15 minutes."
}
```

#### Phase 2: Execute Booking with Confirmation & Idempotency

**Request**:
```bash
curl -X POST http://localhost:8000/api/trips/<TRIP_ID>/booking/confirm \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "pending_action_id": "action_998877",
    "idempotency_key": "user_checkout_attempt_001"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "book_554433",
    "booking_reference": "BK-202611-94821",
    "status": "CONFIRMED",
    "total_amount": 65250.0,
    "currency": "INR",
    "items": [
      {
        "category": "FLIGHT",
        "provider": "MockAirlines",
        "provider_booking_id": "FL-IND-883",
        "price": 18000.0,
        "status": "CONFIRMED"
      },
      {
        "category": "HOTEL",
        "provider": "MockHotels",
        "provider_booking_id": "HT-GOA-502",
        "price": 28000.0,
        "status": "CONFIRMED"
      }
    ]
  },
  "message": "Booking executed successfully. Confirmation vouchers generated."
}
```

---

### Step 8: Disruption Handling & Proactive Rerouting

**Request**:
```bash
curl -X POST http://localhost:8000/api/trips/<TRIP_ID>/disruptions/check \
  -H "Authorization: Bearer <TOKEN>"
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "disrupt_112233",
      "disruption_type": "FLIGHT_CANCELLED",
      "severity": "CRITICAL",
      "reason": "Severe monsoon weather conditions",
      "status": "OPEN",
      "alternative_options": [
        {
          "alternative_id": "ALT-FL-902",
          "provider": "MockAirlines",
          "description": "Next available flight via Mumbai departing +4 hours",
          "price_difference": 0.0,
          "additional_fee": 0.0
        },
        {
          "alternative_id": "ALT-REFUND-FULL",
          "provider": "MockAirlines",
          "description": "Full cash refund for cancelled flight sector",
          "refund_amount": 18000.0
        }
      ]
    }
  ],
  "message": "Disruption detected. Alternatives available for confirmation."
}
```

User confirms resolution:
```bash
curl -X POST http://localhost:8000/api/trips/<TRIP_ID>/disruptions/disrupt_112233/confirm-resolution \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "alternative_id": "ALT-FL-902",
    "idempotency_key": "reschedule_flight_01"
  }'
```

---

## 8. Extensibility: Plugging In Real Travel APIs

To replace mock providers with live Global Distribution Systems (Amadeus, Sabre, Duffel, Booking.com):

1. Implement the abstract provider interfaces in `app/providers/base.py`:
   ```python
   from app.providers.base import FlightProvider

   class AmadeusFlightProvider(FlightProvider):
       async def search_flights(self, origin, destination, departure_date, passengers, **kwargs):
           # Call live Amadeus Self-Service Flight Offers API via httpx
           ...
   ```
2. Bind the new provider class in `app/agents/search_agent.py` or through dependency injection in `app/api/deps.py`.
3. **No changes to LangGraph, agents, database schemas, or confirmation gates are required.**

---

## 9. License

Production-ready backend developed for VOYAGEHACK.
