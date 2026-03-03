"""
dplex - Enterprise-grade data layer framework for Python
"""

__version__ = "0.1.0"

from dplex.dp_filters import DPFilters
from dplex.dp_repo import DPRepo
from dplex.dp_service import DPService
from dplex.exceptions import DplexError, EntityNotFoundError
from dplex.internal.filters import (
    BooleanFilter,
    DateFilter,
    DateTimeFilter,
    DecimalFilter,
    EnumFilter,
    FloatFilter,
    IntFilter,
    StringFilter,
    TimeFilter,
    TimestampFilter,
    UUIDFilter,
    WordsFilter,
)
from dplex.internal.sort import NullsPlacement, Order, Sort

__all__ = [
    # Exceptions
    "DplexError",
    "EntityNotFoundError",
    # Filters
    "StringFilter",
    "IntFilter",
    "FloatFilter",
    "DecimalFilter",
    "BooleanFilter",
    "DateFilter",
    "DateTimeFilter",
    "TimeFilter",
    "TimestampFilter",
    "EnumFilter",
    "UUIDFilter",
    "WordsFilter",
    # Core classes
    "DPRepo",
    "DPService",
    "DPFilters",
    # Sort
    "Sort",
    "Order",
    "NullsPlacement",
]
