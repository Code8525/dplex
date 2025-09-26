"""Ready-to-use filter schemas"""

from dataclasses import dataclass
from datetime import datetime

from .base import FilterSchema


@dataclass
class BaseEntityFilterSchema(FilterSchema):
    """Base filter schema for common entities"""

    # Pagination
    page: int = 1
    per_page: int = 10

    # Sorting
    sort_by: str | None = None
    sort_desc: bool = False

    # Common filters
    created_after: datetime | None = None
    created_before: datetime | None = None
    is_active: bool | None = None
