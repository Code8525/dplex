"""Common types for dplex"""

import uuid
from typing import TypeVar, Union

from sqlalchemy.orm import DeclarativeBase

# Generic types
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
KeyType = TypeVar("KeyType", int, str, uuid.UUID)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
FilterSchemaType = TypeVar("FilterSchemaType")

# Union types for common key types
AnyKeyType = Union[int, str, uuid.UUID]
