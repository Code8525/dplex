"""Base filter schema"""

from dataclasses import dataclass
from typing import Any

from ..repositories.query_builder import QueryBuilder


@dataclass
class FilterSchema:
    """Base filter schema"""

    def apply_filters(self, query: QueryBuilder[Any]) -> QueryBuilder[Any]:
        """Apply filters to query builder"""
        return query
