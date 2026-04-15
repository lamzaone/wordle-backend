class ServiceError(Exception):
    status_code = 400
    detail = "Service error."


class NotFoundError(ServiceError):
    status_code = 404
    detail = "Resource not found."


class ForbiddenError(ServiceError):
    status_code = 403
    detail = "Forbidden."


class ConflictError(ServiceError):
    status_code = 409
    detail = "Conflict."


class ValidationServiceError(ServiceError):
    status_code = 422
    detail = "Invalid input."


class RateLimitError(ServiceError):
    status_code = 429
    detail = "Too many requests."
