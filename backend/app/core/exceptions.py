from typing import Any, Optional
from fastapi import HTTPException, status


class TravelAppException(Exception):
    """Base exception for all application errors."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ResourceNotFoundException(TravelAppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with ID '{identifier}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)}
        )


class UnauthorizedException(TravelAppException):
    def __init__(self, message: str = "Invalid credentials or token expired."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(TravelAppException):
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN
        )


class ValidationException(TravelAppException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details
        )


class StalePricingException(TravelAppException):
    def __init__(self, message: str = "Price quote has expired or changed. Please re-search.", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="STALE_PRICING",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class ProviderUnavailableException(TravelAppException):
    def __init__(self, provider: str, details: Optional[Any] = None):
        super().__init__(
            message=f"Travel provider '{provider}' is temporarily unavailable. Gracefully operating on mock/cached fallback.",
            code="PROVIDER_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class DuplicateActionException(TravelAppException):
    def __init__(self, action: str, idempotency_key: str):
        super().__init__(
            message=f"Duplicate request detected for action '{action}' with key '{idempotency_key}'.",
            code="DUPLICATE_ACTION",
            status_code=status.HTTP_409_CONFLICT,
            details={"action": action, "idempotency_key": idempotency_key}
        )


class ConfirmationRequiredException(TravelAppException):
    def __init__(self, action: str, pending_action_id: str):
        super().__init__(
            message=f"Action '{action}' requires explicit human confirmation before execution.",
            code="CONFIRMATION_REQUIRED",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"action": action, "pending_action_id": pending_action_id}
        )


class ExpiredConfirmationException(TravelAppException):
    def __init__(self, pending_action_id: str):
        super().__init__(
            message="Confirmation window has expired. Please review and request again.",
            code="CONFIRMATION_EXPIRED",
            status_code=status.HTTP_410_GONE,
            details={"pending_action_id": pending_action_id}
        )
