"""Dataplex exceptions"""


class DataplexException(Exception):
    """Base Dataplex exception"""
    pass


class RepositoryError(DataplexException):
    """Repository related errors"""
    pass


class ServiceError(DataplexException):
    """Service related errors"""
    pass


class FilterError(DataplexException):
    """Filter related errors"""
    pass


class CacheError(DataplexException):
    """Cache related errors"""
    pass


class AuditError(DataplexException):
    """Audit related errors"""
    pass


class ValidationError(DataplexException):
    """Validation related errors"""
    pass
