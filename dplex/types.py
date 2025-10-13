import uuid
from enum import Enum, StrEnum
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
    FloatFilter,
    DecimalFilter,
    BaseNumberFilter,
    TimeFilter,
    IntFilter,
    EnumFilter,
    UUIDFilter,
)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

KeyType = TypeVar("KeyType", int, str, uuid.UUID)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
FilterSchemaType = TypeVar("FilterSchemaType")

SortFieldSchemaType = TypeVar("SortFieldSchemaType")

# Generic type для поля сортировки
SortFieldType = TypeVar("SortFieldType", bound=StrEnum)

FilterType = (
    StringFilter
    | IntFilter
    | FloatFilter
    | DecimalFilter
    | BaseNumberFilter
    | DateTimeFilter
    | DateFilter
    | TimeFilter
    | TimestampFilter
    | BooleanFilter
    | EnumFilter
    | UUIDFilter
)
