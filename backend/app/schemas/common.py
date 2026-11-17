from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    details: Optional[Any] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str = "Operation successful"
    error: Optional[ErrorDetail] = None

    @classmethod
    def ok(cls, data: Optional[T] = None, message: str = "Success") -> "APIResponse[T]":
        return cls(success=True, data=data, message=message, error=None)

    @classmethod
    def fail(cls, message: str, code: str = "ERROR", details: Optional[Any] = None) -> "APIResponse[T]":
        return cls(
            success=False,
            data=None,
            message=message,
            error=ErrorDetail(code=code, details=details)
        )
