"""Custom exception classes and global error handlers for NIRMAYA API."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, List
from datetime import datetime, timezone
from app.schemas.common import ErrorDetail


class AppException(Exception):
    """Base application exception for clinical business logic errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "APPLICATION_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or []


class EntityNotFoundException(AppException):
    """Raised when a requested patient, doctor, or record entity is absent."""

    def __init__(self, entity_name: str, entity_id: str):
        super().__init__(
            message=f"{entity_name} with identifier '{entity_id}' not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PermissionDeniedException(AppException):
    """Raised when an actor lacks sufficient role permissions or consent authorization."""

    def __init__(self, message: str = "Access to requested health resource is forbidden"):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class AuthenticationException(AppException):
    """Raised when request lacks valid authentication credentials or bearer token is invalid."""

    def __init__(
        self,
        message: str = "Authentication credentials were not provided or are invalid",
        error_code: str = "AUTHENTICATION_REQUIRED",
        headers: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        self.headers = headers or {"WWW-Authenticate": "Bearer"}


def register_exception_handlers(app):
    """Register uniform error handlers formatting failures into standard ErrorResponse JSON."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        request_id = getattr(request.state, "request_id", None)
        headers = getattr(exc, "headers", None)
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": [d.model_dump() if hasattr(d, "model_dump") else d for d in exc.details],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        formatted_details = []
        for error in exc.errors():
            loc = " -> ".join([str(x) for x in error.get("loc", [])])
            formatted_details.append(
                {
                    "location": loc,
                    "message": error.get("msg", "Validation error"),
                    "error_type": error.get("type", "value_error"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Input validation failed for request parameters or payload",
                "details": formatted_details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing the clinical transaction",
                "details": [{"message": str(exc)}] if app.debug else [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
            },
        )
