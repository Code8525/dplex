"""Typed filter operators"""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class NumericFilter(Generic[T]):
    """Numeric filter operators"""

    eq: T | None = None
    ne: T | None = None
    gt: T | None = None
    gte: T | None = None
    lt: T | None = None
    lte: T | None = None
    in_: list[T] | None = None


@dataclass
class StringFilter:
    """String filter operators"""

    eq: str | None = None
    ne: str | None = None
    like: str | None = None
    ilike: str | None = None
    in_: list[str] | None = None


@dataclass
class BoolFilter:
    """Boolean filter operators"""

    eq: bool | None = None
