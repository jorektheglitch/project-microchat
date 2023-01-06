from abc import ABC


class ServiceError(ABC, Exception):
    pass


class AccessDenied(ServiceError):
    pass


class DoesNotExists(ServiceError):
    pass
