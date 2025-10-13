import datetime
from typing import Any, Protocol

from dplex.services.filters import (
    StringFilter,
    DateTimeFilter,
    NumberFilter,
    BooleanFilter,
)
from dplex.services.types import FilterType


class SupportsFiltering(Protocol):
    """Protocol for query builders that support filtering operations"""

    def where_eq(self, column: Any, value: Any) -> Any: ...

    def where_ne(self, column: Any, value: Any) -> Any: ...

    def where_in(self, column: Any, values: list[Any]) -> Any: ...

    def where_not_in(self, column: Any, values: list[Any]) -> Any: ...

    def where_is_null(self, column: Any) -> Any: ...

    def where_is_not_null(self, column: Any) -> Any: ...

    def where_gt(self, column: Any, value: Any) -> Any: ...

    def where_gte(self, column: Any, value: Any) -> Any: ...

    def where_lt(self, column: Any, value: Any) -> Any: ...

    def where_lte(self, column: Any, value: Any) -> Any: ...

    def where_between(self, column: Any, start: Any, end: Any) -> Any: ...

    def where_like(self, column: Any, pattern: str) -> Any: ...

    def where_ilike(self, column: Any, pattern: str) -> Any: ...


class FilterApplier:
    """Класс для применения базовых фильтров к query builder"""

    # String operation keys for type detection
    _STRING_OPS = frozenset(
        ["contains", "icontains", "starts_with", "ends_with", "like", "ilike"]
    )

    # Comparison operation keys for type detection
    _COMPARISON_OPS = frozenset(["gt", "gte", "lt", "lte", "between"])

    @staticmethod
    def _apply_common_ops(
        query_builder: SupportsFiltering, column: Any, filter_data: FilterType
    ) -> SupportsFiltering:
        """Применить общие операции сравнения (eq, ne, in, is_null)"""
        if filter_data.eq is not None:
            query_builder = query_builder.where_eq(column, filter_data.eq)

        if filter_data.ne is not None:
            query_builder = query_builder.where_ne(column, filter_data.ne)

        if hasattr(filter_data, "in_") and filter_data.in_ is not None:
            query_builder = query_builder.where_in(column, filter_data.in_)

        if hasattr(filter_data, "not_in") and filter_data.not_in is not None:
            query_builder = query_builder.where_not_in(column, filter_data.not_in)

        if getattr(filter_data, "is_null", None) is True:
            query_builder = query_builder.where_is_null(column)

        if getattr(filter_data, "is_not_null", None) is True:
            query_builder = query_builder.where_is_not_null(column)

        return query_builder

    @staticmethod
    def _apply_comparison_ops(
        query_builder: SupportsFiltering,
        column: Any,
        filter_data: NumberFilter | DateTimeFilter,
    ) -> SupportsFiltering:
        """Применить операции сравнения для чисел и дат (gt, gte, lt, lte, between)"""
        if filter_data.gt is not None:
            query_builder = query_builder.where_gt(column, filter_data.gt)

        if filter_data.gte is not None:
            query_builder = query_builder.where_gte(column, filter_data.gte)

        if filter_data.lt is not None:
            query_builder = query_builder.where_lt(column, filter_data.lt)

        if filter_data.lte is not None:
            query_builder = query_builder.where_lte(column, filter_data.lte)

        if filter_data.between is not None:
            start, end = filter_data.between
            query_builder = query_builder.where_between(column, start, end)

        return query_builder

    @staticmethod
    def _apply_string_ops(
        query_builder: SupportsFiltering, column: Any, filter_data: StringFilter
    ) -> SupportsFiltering:
        """Применить строковые операции (like, ilike, contains, starts_with, ends_with)"""
        if filter_data.like is not None:
            query_builder = query_builder.where_like(column, filter_data.like)

        if filter_data.ilike is not None:
            query_builder = query_builder.where_ilike(column, filter_data.ilike)

        if filter_data.contains is not None:
            pattern = f"%{filter_data.contains}%"
            query_builder = query_builder.where_like(column, pattern)

        if filter_data.icontains is not None:
            pattern = f"%{filter_data.icontains}%"
            query_builder = query_builder.where_ilike(column, pattern)

        if filter_data.starts_with is not None:
            pattern = f"{filter_data.starts_with}%"
            query_builder = query_builder.where_like(column, pattern)

        if filter_data.ends_with is not None:
            pattern = f"%{filter_data.ends_with}"
            query_builder = query_builder.where_like(column, pattern)

        return query_builder

    def apply_string_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: StringFilter
    ) -> SupportsFiltering:
        """Применить строковый фильтр"""
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        query_builder = self._apply_string_ops(query_builder, column, filter_data)
        return query_builder

    def apply_number_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: NumberFilter
    ) -> SupportsFiltering:
        """Применить числовой фильтр"""
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        query_builder = self._apply_comparison_ops(query_builder, column, filter_data)
        return query_builder

    def apply_datetime_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: DateTimeFilter
    ) -> SupportsFiltering:
        """Применить datetime фильтр"""
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        query_builder = self._apply_comparison_ops(query_builder, column, filter_data)
        return query_builder

    def apply_boolean_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: BooleanFilter
    ) -> SupportsFiltering:
        """Применить boolean фильтр"""
        return self._apply_common_ops(query_builder, column, filter_data)

    def _detect_filter_type(
        self, field_value: dict[str, Any]
    ) -> type[StringFilter | NumberFilter | DateTimeFilter | BooleanFilter] | None:
        """
        Определить тип фильтра по содержимому словаря

        Приоритет определения:
        1. По специфичным строковым операциям
        2. По операциям сравнения
        3. По типу значения в 'eq'
        """
        # Проверяем строковые операции
        if any(op in field_value for op in self._STRING_OPS):
            return StringFilter

        # Проверяем операции сравнения
        if any(op in field_value for op in self._COMPARISON_OPS):
            return self._detect_comparison_filter_type(field_value)

        # Определяем по значению eq
        if "eq" in field_value:
            return self._detect_filter_type_by_value(field_value["eq"])

        return None

    @staticmethod
    def _detect_comparison_filter_type(
        field_value: dict[str, Any],
    ) -> type[NumberFilter | DateTimeFilter]:
        """Определить тип фильтра сравнения по типу первого значения"""
        first_value = next((v for v in field_value.values() if v is not None), None)

        if isinstance(first_value, datetime.datetime):
            return DateTimeFilter

        return NumberFilter

    @staticmethod
    def _detect_filter_type_by_value(
        value: Any,
    ) -> type[StringFilter | NumberFilter | DateTimeFilter | BooleanFilter] | None:
        """Определить тип фильтра по типу значения"""
        if isinstance(value, bool):
            return BooleanFilter

        if isinstance(value, str):
            return StringFilter

        if isinstance(value, (int, float)):
            return NumberFilter

        if isinstance(value, datetime.datetime):
            return DateTimeFilter

        return None

    def _apply_filter_by_type(
        self,
        query_builder: SupportsFiltering,
        column: Any,
        filter_type: type[FilterType],
        field_value: dict[str, Any],
    ) -> SupportsFiltering:
        """Применить фильтр определенного типа"""
        filter_obj = filter_type(**field_value)

        if filter_type == StringFilter:
            return self.apply_string_filter(query_builder, column, filter_obj)

        if filter_type == NumberFilter:
            return self.apply_number_filter(query_builder, column, filter_obj)

        if filter_type == DateTimeFilter:
            return self.apply_datetime_filter(query_builder, column, filter_obj)

        if filter_type == BooleanFilter:
            return self.apply_boolean_filter(query_builder, column, filter_obj)

        return query_builder

    def apply_filters_from_schema(
        self,
        query_builder: SupportsFiltering,
        model: type,
        filterable_fields: FilterableFields,
    ) -> SupportsFiltering:
        """
        Применить все фильтры из схемы FilterableFields автоматически

        Args:
            query_builder: Query builder для применения фильтров
            model: SQLAlchemy модель с колонками
            filterable_fields: Схема с фильтрами

        Returns:
            Query builder с примененными фильтрами
        """
        fields_dict = filterable_fields.model_dump(exclude_none=True)

        for field_name, field_value in fields_dict.items():
            # Пропускаем невалидные значения
            if field_value is None or not isinstance(field_value, dict):
                continue

            # Пропускаем поля, отсутствующие в модели
            if not hasattr(model, field_name):
                continue

            column = getattr(model, field_name)

            # Определяем и применяем фильтр
            filter_type = self._detect_filter_type(field_value)

            if filter_type is not None:
                query_builder = self._apply_filter_by_type(
                    query_builder, column, filter_type, field_value
                )

        return query_builder
