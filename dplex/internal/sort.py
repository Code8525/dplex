"""Классы для описания сортировки данных в запросах"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic

from dplex.internal.types import SortByType


class Order(StrEnum):
    """
    Направление сортировки

    Определяет порядок сортировки элементов: по возрастанию или убыванию.
    Используется в SQL ORDER BY clause.

    Attributes:
        ASC: По возрастанию (ascending). От меньшего к большему, от A до Z
        DESC: По убыванию (descending). От большего к меньшему, от Z до A

    Examples:
        >>> Order.ASC
        'asc'
        >>> Order.DESC
        'desc'
    """

    ASC = "asc"
    DESC = "desc"


class NullsPlacement(StrEnum):
    """
    Размещение NULL значений при сортировке

    Определяет, где должны располагаться NULL значения в отсортированном результате.
    Используется в SQL NULLS FIRST/LAST clause.

    Attributes:
        FIRST: NULL значения в начале результата
        LAST: NULL значения в конце результата

    Examples:
        >>> NullsPlacement.FIRST
        'first'
        >>> NullsPlacement.LAST
        'last'

    Notes:
        Поведение по умолчанию различается в разных СУБД:
        - PostgreSQL: NULLS LAST для ASC, NULLS FIRST для DESC
        - SQLite: NULLS FIRST для ASC, NULLS LAST для DESC
    """

    FIRST = "first"
    LAST = "last"


@dataclass(frozen=True)
class Sort(Generic[SortByType]):
    """
    Элемент сортировки для запросов

    Описывает правило сортировки: по какому полю, в каком направлении
    и как обрабатывать NULL значения.

    Type Parameters:
        SortByType: Тип поля для сортировки (обычно str или Enum)

    Attributes:
        by: Поле для сортировки
        order: Направление сортировки (по умолчанию ASC)
        nulls: Размещение NULL значений (по умолчанию None - поведение СУБД)


    Notes:
        - Класс immutable (frozen=True) для безопасного использования в хешируемых структурах
        - Параметр nulls опционален - если None, используется поведение СУБД по умолчанию
    """

    by: SortByType
    order: Order = Order.ASC
    nulls: NullsPlacement | None = None
