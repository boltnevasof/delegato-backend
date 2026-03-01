from typing import Any


class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None, **kwargs: Any) -> None:
        self.detail = detail or self.__class__.detail
        self.extra = kwargs
        super().__init__(self.detail)


class NotFound(AppException):
    status_code = 404
    detail = "Resource not found"


class Forbidden(AppException):
    status_code = 403
    detail = "Access forbidden"


class Unauthorized(AppException):
    status_code = 401
    detail = "Not authenticated"


class BadRequest(AppException):
    status_code = 400
    detail = "Bad request"


class ConflictError(AppException):
    status_code = 409
    detail = "Resource conflict"


class RateLimitExceeded(AppException):
    status_code = 429
    detail = "Rate limit exceeded"


class ExternalServiceError(AppException):
    status_code = 502
    detail = "External service error"
