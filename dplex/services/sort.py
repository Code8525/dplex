from enum import StrEnum
from dataclasses import dataclass
from typing import TypeVar, Generic

from dplex.types import SortFieldType


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class NullsPlacement(StrEnum):
    FIRST = "first"
    LAST = "last"


@dataclass(frozen=True)
class Sort(Generic[SortFieldType]):
    """Элемент сортировки"""

    field: SortFieldType
    direction: SortDirection = SortDirection.ASC
    nulls: NullsPlacement | None = None
