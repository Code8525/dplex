"""Типы данных для системы фильтрации, сортировки и работы с моделями"""

import uuid
from enum import StrEnum
from typing import TypeVar, TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

# Используем TYPE_CHECKING для избежания циклических импортов
from dplex.internal.filters import (
    StringFilter,
    IntFilter,
    FloatFilter,
    DecimalFilter,
    DateTimeFilter,
    DateFilter,
    TimeFilter,
    TimestampFilter,
    BooleanFilter,
    EnumFilter,
    UUIDFilter,
    WordsFilter,
)

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
"""
TypeVar для SQLAlchemy моделей

Используется для типизации методов репозиториев и сервисов,
работающих с моделями базы данных.
"""

KeyType = TypeVar("KeyType", int, str, uuid.UUID)
"""
TypeVar для типов первичных ключей

Ограничен стандартными типами первичных ключей:
- int: Автоинкрементные числовые ID
- str: Строковые идентификаторы
- uuid.UUID: UUID идентификаторы
"""

ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
"""
TypeVar для Pydantic схем ответа

Используется для типизации схем, возвращаемых из API endpoints.
Должен быть подклассом BaseModel от Pydantic.
"""

CreateSchemaType = TypeVar("CreateSchemaType")
"""
TypeVar для схем создания записей

Используется для типизации данных при создании новых записей в БД.
Обычно это Pydantic модели без полей id, created_at и т.д.
"""

UpdateSchemaType = TypeVar("UpdateSchemaType")
"""
TypeVar для схем обновления записей

Используется для типизации данных при обновлении существующих записей.
Обычно все поля опциональны для частичного обновления (PATCH).
"""

FilterSchemaType = TypeVar("FilterSchemaType")
"""
TypeVar для схем фильтрации

Используется для типизации схем, содержащих параметры фильтрации.
Обычно наследуется от DPFilters.
"""

SortFieldSchemaType = TypeVar("SortFieldSchemaType")
"""
TypeVar для схем полей сортировки

Используется для типизации доступных полей для сортировки.
Обычно это StrEnum с именами полей модели.
"""

SortByType = TypeVar("SortByType", bound=StrEnum)
"""
TypeVar для типа поля сортировки

Ограничен StrEnum для обеспечения типобезопасности при сортировке.
Используется в Sort[SortByType] и DPFilters[SortByType].
"""
# Определяем FilterType только для type checkers
FilterType = (
    StringFilter
    | IntFilter
    | FloatFilter
    | DecimalFilter
    | DateTimeFilter
    | DateFilter
    | TimeFilter
    | TimestampFilter
    | BooleanFilter
    | EnumFilter
    | UUIDFilter
    | WordsFilter
)
"""
Union тип всех доступных фильтров

Используется для типизации методов, принимающих любой тип фильтра.
Включает все специализированные классы фильтров из dplex.services.filters.

Типы фильтров:
    - StringFilter: Фильтрация строковых полей
    - IntFilter: Фильтрация целых чисел
    - FloatFilter: Фильтрация чисел с плавающей точкой
    - DecimalFilter: Фильтрация точных десятичных чисел
    - DateTimeFilter: Фильтрация даты и времени
    - DateFilter: Фильтрация только дат
    - TimeFilter: Фильтрация только времени
    - TimestampFilter: Фильтрация Unix timestamp
    - BooleanFilter: Фильтрация булевых значений
    - EnumFilter: Фильтрация enum полей
    - UUIDFilter: Фильтрация UUID полей
    - WordsFilter: Фильтр для поиска по нескольким словам с автоматической разбивкой
"""
