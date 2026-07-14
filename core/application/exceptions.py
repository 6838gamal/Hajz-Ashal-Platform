"""Exceptions reserved for unexpected/system failures. Expected business
failures should be returned as a failed Result instead of raised here -
these are caught centrally and mapped to HTTP responses in
core/presentation/error_handlers.py."""


class DomainException(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundException(DomainException):
    code = "NOT_FOUND"


class ConflictException(DomainException):
    code = "CONFLICT"


class ValidationException(DomainException):
    code = "VALIDATION_ERROR"


class UnauthorizedException(DomainException):
    code = "UNAUTHORIZED"


class ForbiddenException(DomainException):
    code = "FORBIDDEN"


class UsageLimitExceededException(DomainException):
    code = "USAGE_LIMIT_EXCEEDED"
