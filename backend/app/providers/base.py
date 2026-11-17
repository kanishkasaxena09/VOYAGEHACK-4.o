from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional


class FlightProvider(ABC):
    @abstractmethod
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[date] = None,
        return_date: Optional[date] = None,
        passengers: int = 1,
        cabin_class: Optional[str] = "economy",
        nonstop_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Search available flights."""
        pass

    @abstractmethod
    async def get_flight_details(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get flight pricing and availability details."""
        pass


class HotelProvider(ABC):
    @abstractmethod
    async def search_hotels(
        self,
        city: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        guests: int = 2,
        category: Optional[str] = None,
        max_price_per_night: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search available hotels."""
        pass

    @abstractmethod
    async def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get hotel pricing and availability details."""
        pass


class ActivityProvider(ABC):
    @abstractmethod
    async def search_activities(
        self,
        city: str,
        category: Optional[str] = None,
        activity_date: Optional[date] = None,
        participants: int = 2
    ) -> List[Dict[str, Any]]:
        """Search activities and tours."""
        pass

    @abstractmethod
    async def get_activity_details(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Get activity pricing and availability details."""
        pass


class TransferProvider(ABC):
    @abstractmethod
    async def search_transfers(
        self,
        city: str,
        passengers: int = 2,
        vehicle_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search airport and city transfers."""
        pass

    @abstractmethod
    async def get_transfer_details(self, transfer_id: str) -> Optional[Dict[str, Any]]:
        """Get transfer pricing and availability details."""
        pass


class BookingProvider(ABC):
    @abstractmethod
    async def create_booking(
        self,
        trip_id: str,
        user_id: str,
        components: List[Dict[str, Any]],
        idempotency_key: str
    ) -> Dict[str, Any]:
        """Execute booking against provider."""
        pass

    @abstractmethod
    async def cancel_booking(
        self,
        booking_reference: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel an existing booking."""
        pass

    @abstractmethod
    async def modify_booking(
        self,
        booking_reference: str,
        modification_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify an existing booking."""
        pass
