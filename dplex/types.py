import uuid
from enum import Enum
from typing import TypeVar, Union, Any

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

from dplex.services.filters import (
    StringFilter,
    DateTimeFilter,
    NumberFilter,
    BooleanFilter,
    DateFilter,
    TimestampFilter,
)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

KeyType = TypeVar("KeyType", int, str, uuid.UUID)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
FilterSchemaType = TypeVar("FilterSchemaType")

AnyKeyType = Union[int, str, uuid.UUID]
SortFieldSchemaType = TypeVar("SortFieldSchemaType")

FilterType = (
    StringFilter
    | NumberFilter
    | DateTimeFilter
    | DateFilter
    | TimestampFilter
    | BooleanFilter
)


class SortDirection(str, Enum):
    """Направления сортировки"""

    ASC = "ASC"
    DESC = "DESC"
