"""Custom application exceptions with standard error codes."""


class AttendXException(Exception):
    """Base exception for all AttendX application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
    ):
        if message is not None:
            self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AttendXException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found."


class ValidationException(AttendXException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed."


class AuthenticationException(AttendXException):
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
    message = "Could not validate credentials."


class AuthorizationException(AttendXException):
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"
    message = "You do not have permission to perform this action."


class DeviceException(AttendXException):
    status_code = 502
    error_code = "DEVICE_ERROR"
    message = "Device communication error."


class DuplicateException(AttendXException):
    status_code = 409
    error_code = "DUPLICATE"
    message = "A resource with this identifier already exists."


class RateLimitException(AttendXException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later."
