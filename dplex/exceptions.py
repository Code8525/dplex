"""dplex exceptions"""


class dplexException(Exception):
    """Base dplex exception"""
    pass


class RepositoryError(dplexException):
    """Repository related errors"""
    pass


class ServiceError(dplexException):
    """Service related errors"""
    pass


class FilterError(dplexException):
    """Filter related errors"""
    pass


class CacheError(dplexException):
    """Cache related errors"""
    pass


class AuditError(dplexException):
    """Audit related errors"""
    pass


class ValidationError(dplexException):
    """Validation related errors"""
    pass
