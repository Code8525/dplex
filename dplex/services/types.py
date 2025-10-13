from typing import TypeVar

from dplex.services.filters import (
    StringFilter,
    DateTimeFilter,
    NumberFilter,
    BooleanFilter,
)


FilterType = StringFilter | NumberFilter | DateTimeFilter | BooleanFilter
