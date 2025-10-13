# file: dplex/services/simple_filter_builder.py
"""
Самый простой способ создания типизированных фильтров
"""
from typing import Any, get_type_hints

from dplex.services.base_filterable_fields import BaseFilterableFields
from dplex.services.filters import (
    StringFilter,
    NumberFilter,
    BooleanFilter,
    DateTimeFilter,
)


def create_filter_builder(schema_class: type[BaseFilterableFields]) -> type:
    """
    Автоматически создает типизированный builder для схемы фильтров

    Args:
        schema_class: Класс схемы фильтров (наследник BaseFilterableFields)

    Returns:
        Класс builder'а с автодополнением

    Example:
        ```python
        class UserFilterableFields(BaseFilterableFields):
            name: StringFilter | None = None
            age: NumberFilter[int] | None = None

        # Автоматически создает типизированный builder
        UserFilter = create_filter_builder(UserFilterableFields)

        # Использование с автодополнением
        filters = UserFilter().name.icontains("john").age.gte(18).build()
        ```
    """

    class DynamicFilterBuilder:
        def __init__(self) -> None:
            self.schema_class = schema_class
            self.filters: dict[str, dict[str, Any]] = {}

        def add_filter(
            self, field: str, operation: str, value: Any
        ) -> "DynamicFilterBuilder":
            """Добавить фильтр"""
            if field not in self.filters:
                self.filters[field] = {}
            self.filters[field][operation] = value
            return self

        def build(self) -> BaseFilterableFields:
            """Построить схему фильтров"""
            return self.schema_class(**self.filters)

    # Получаем аннотации типов из схемы
    type_hints = get_type_hints(schema_class)

    # Для каждого поля создаем property
    for field_name, field_type in type_hints.items():
        if field_name.startswith("_"):
            continue

        # Определяем тип фильтра
        filter_type = _extract_filter_type(field_type)

        # Создаем соответствующий FieldBuilder
        if filter_type == StringFilter:
            field_builder_class = _create_string_field_property(field_name)
        elif filter_type in (NumberFilter, int, float):
            field_builder_class = _create_number_field_property(field_name)
        elif filter_type == BooleanFilter:
            field_builder_class = _create_boolean_field_property(field_name)
        elif filter_type == DateTimeFilter:
            field_builder_class = _create_datetime_field_property(field_name)
        else:
            continue

        setattr(DynamicFilterBuilder, field_name, field_builder_class)

    return DynamicFilterBuilder


def _extract_filter_type(field_type: Any) -> type | None:
    """Извлечь тип фильтра из аннотации"""
    # Обработка Optional (Type | None)
    if hasattr(field_type, "__args__"):
        for arg in field_type.__args__:
            if arg is type(None):
                continue
            # Обработка Generic типов (NumberFilter[int])
            if hasattr(arg, "__origin__"):
                return arg.__origin__
            return arg
    return field_type


def _create_string_field_property(field_name: str) -> property:
    """Создать property для строкового поля"""

    class StringField:
        def __init__(self, parent: Any) -> None:
            self.parent = parent

        def eq(self, value: str) -> Any:
            return self.parent.add_filter(field_name, "eq", value)

        def ne(self, value: str) -> Any:
            return self.parent.add_filter(field_name, "ne", value)

        def contains(self, value: str) -> Any:
            return self.parent.add_filter(field_name, "contains", value)

        def icontains(self, value: str) -> Any:
            return self.parent.add_filter(field_name, "icontains", value)

        def starts_with(self, value: str) -> Any:
            return self.parent.add_filter(field_name, "starts_with", value)

        def ends_with(self, value: str) -> Any:
            return self.parent.add_filter(field_name, "ends_with", value)

        def like(self, pattern: str) -> Any:
            return self.parent.add_filter(field_name, "like", pattern)

        def ilike(self, pattern: str) -> Any:
            return self.parent.add_filter(field_name, "ilike", pattern)

        def in_(self, values: list[str]) -> Any:
            return self.parent.add_filter(field_name, "in_", values)

        def not_in(self, values: list[str]) -> Any:
            return self.parent.add_filter(field_name, "not_in", values)

        def is_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_null", True)

        def is_not_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_not_null", True)

    return property(lambda self: StringField(self))


def _create_number_field_property(field_name: str) -> property:
    """Создать property для числового поля"""

    class NumberField:
        def __init__(self, parent: Any) -> None:
            self.parent = parent

        def eq(self, value: int | float) -> Any:
            return self.parent.add_filter(field_name, "eq", value)

        def ne(self, value: int | float) -> Any:
            return self.parent.add_filter(field_name, "ne", value)

        def gt(self, value: int | float) -> Any:
            return self.parent.add_filter(field_name, "gt", value)

        def gte(self, value: int | float) -> Any:
            return self.parent.add_filter(field_name, "gte", value)

        def lt(self, value: int | float) -> Any:
            return self.parent.add_filter(field_name, "lt", value)

        def lte(self, value: int | float) -> Any:
            return self.parent.add_filter(field_name, "lte", value)

        def between(self, start: int | float, end: int | float) -> Any:
            return self.parent.add_filter(field_name, "between", (start, end))

        def in_(self, values: list[int | float]) -> Any:
            return self.parent.add_filter(field_name, "in_", values)

        def not_in(self, values: list[int | float]) -> Any:
            return self.parent.add_filter(field_name, "not_in", values)

        def is_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_null", True)

        def is_not_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_not_null", True)

    return property(lambda self: NumberField(self))


def _create_boolean_field_property(field_name: str) -> property:
    """Создать property для булевого поля"""

    class BooleanField:
        def __init__(self, parent: Any) -> None:
            self.parent = parent

        def eq(self, value: bool) -> Any:
            return self.parent.add_filter(field_name, "eq", value)

        def ne(self, value: bool) -> Any:
            return self.parent.add_filter(field_name, "ne", value)

        def is_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_null", True)

        def is_not_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_not_null", True)

    return property(lambda self: BooleanField(self))


def _create_datetime_field_property(field_name: str) -> property:
    """Создать property для поля даты/времени"""
    from datetime import datetime, date

    class DateTimeField:
        def __init__(self, parent: Any) -> None:
            self.parent = parent

        def eq(self, value: datetime | date) -> Any:
            return self.parent.add_filter(field_name, "eq", value)

        def ne(self, value: datetime | date) -> Any:
            return self.parent.add_filter(field_name, "ne", value)

        def gt(self, value: datetime | date) -> Any:
            return self.parent.add_filter(field_name, "gt", value)

        def gte(self, value: datetime | date) -> Any:
            return self.parent.add_filter(field_name, "gte", value)

        def lt(self, value: datetime | date) -> Any:
            return self.parent.add_filter(field_name, "lt", value)

        def lte(self, value: datetime | date) -> Any:
            return self.parent.add_filter(field_name, "lte", value)

        def between(self, start: datetime | date, end: datetime | date) -> Any:
            return self.parent.add_filter(field_name, "between", (start, end))

        def in_(self, values: list[datetime | date]) -> Any:
            return self.parent.add_filter(field_name, "in_", values)

        def not_in(self, values: list[datetime | date]) -> Any:
            return self.parent.add_filter(field_name, "not_in", values)

        def is_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_null", True)

        def is_not_null(self) -> Any:
            return self.parent.add_filter(field_name, "is_not_null", True)

    return property(lambda self: DateTimeField(self))
