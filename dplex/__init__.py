"""
dplex - Enterprise-grade data layer framework for Python
"""

from dplex.repositories.dp_repo import DPRepo
from dplex.services.dp_service import DPService
from dplex.services.dp_filters import DPFilters
from dplex.services.sort import Sort, Order, NullsPlacement
from dplex.services.filters import (
    StringFilter,
    IntFilter,
    FloatFilter,
    DecimalFilter,
    BooleanFilter,
    DateFilter,
    DateTimeFilter,
    TimeFilter,
    TimestampFilter,
    EnumFilter,
    UUIDFilter,
)

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "DPRepo",
    "DPService",
    "DPFilters",
    # Sort
    "Sort",
    "Order",
    "NullsPlacement",
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
]
