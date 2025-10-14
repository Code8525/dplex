from enum import StrEnum
from dataclasses import dataclass
from typing import Generic

from dplex.types import SortByType


class Order(StrEnum):
    ASC = "asc"
    DESC = "desc"


class NullsPlacement(StrEnum):
    FIRST = "first"
    LAST = "last"


@dataclass(frozen=True)
class Sort(Generic[SortByType]):
    """Элемент сортировки"""

    by: SortByType
    order: Order = Order.ASC
    nulls: NullsPlacement | None = None
