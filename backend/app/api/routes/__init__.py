from fastapi import APIRouter
from app.api.routes.auth import router as auth_router
from app.api.routes.trips import router as trips_router
from app.api.routes.chat import router as chat_router
from app.api.routes.destinations import router as destinations_router
from app.api.routes.itinerary import router as itinerary_router
from app.api.routes.search import router as search_router
from app.api.routes.pricing import router as pricing_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.disruptions import router as disruptions_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(trips_router)
api_router.include_router(chat_router)
api_router.include_router(destinations_router)
api_router.include_router(itinerary_router)
api_router.include_router(search_router)
api_router.include_router(pricing_router)
api_router.include_router(bookings_router)
api_router.include_router(disruptions_router)
