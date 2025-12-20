"""
dplex - Enterprise-grade data layer framework for Python
"""

__version__ = "0.1.0"

__all__ = [
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


from dplex.internal.sort import NullsPlacement, Order, Sort


from dplex.internal.filters import (
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
    WordsFilter,
)


from dplex.dp_filters import DPFilters

from dplex.dp_repo import DPRepo


from dplex.dp_service import DPService
