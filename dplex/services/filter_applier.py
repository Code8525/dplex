import datetime
from typing import Any, Protocol

from dplex.services.base_filterable_fields import BaseFilterableFields
from dplex.services.filters import (
    StringFilter,
    DateTimeFilter,
    NumberFilter,
    BooleanFilter,
)
from dplex.types import FilterType


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
        """Применить общие операции фильтрации (eq, ne, in_, not_in, is_null, is_not_null)"""
        if filter_data.eq is not None:
            query_builder = query_builder.where_eq(column, filter_data.eq)

        if filter_data.ne is not None:
            query_builder = query_builder.where_ne(column, filter_data.ne)

        if filter_data.in_ is not None:
            query_builder = query_builder.where_in(column, filter_data.in_)

        if filter_data.not_in is not None:
            query_builder = query_builder.where_not_in(column, filter_data.not_in)

        if filter_data.is_null is not None and filter_data.is_null:
            query_builder = query_builder.where_is_null(column)

        if filter_data.is_not_null is not None and filter_data.is_not_null:
            query_builder = query_builder.where_is_not_null(column)

        return query_builder

    @staticmethod
    def _apply_comparison_ops(
        query_builder: SupportsFiltering,
        column: Any,
        filter_data: NumberFilter | DateTimeFilter,
    ) -> SupportsFiltering:
        """Применить операции сравнения (gt, gte, lt, lte, between)"""
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
        """Применить строковые операции (like, ilike, contains, etc.)"""
        if filter_data.like is not None:
            query_builder = query_builder.where_like(column, filter_data.like)

        if filter_data.ilike is not None:
            query_builder = query_builder.where_ilike(column, filter_data.ilike)

        if filter_data.contains is not None:
            query_builder = query_builder.where_like(
                column, f"%{filter_data.contains}%"
            )

        if filter_data.icontains is not None:
            query_builder = query_builder.where_ilike(
                column, f"%{filter_data.icontains}%"
            )

        if filter_data.starts_with is not None:
            query_builder = query_builder.where_like(
                column, f"{filter_data.starts_with}%"
            )

        if filter_data.ends_with is not None:
            query_builder = query_builder.where_like(
                column, f"%{filter_data.ends_with}"
            )

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
        """Применить фильтр даты/времени"""
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        query_builder = self._apply_comparison_ops(query_builder, column, filter_data)
        return query_builder

    def apply_boolean_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: BooleanFilter
    ) -> SupportsFiltering:
        """Применить булевый фильтр"""
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        return query_builder

    def apply_filters_from_schema(
        self,
        query_builder: SupportsFiltering,
        model: type,
        filterable_fields: BaseFilterableFields,
    ) -> SupportsFiltering:
        """
        Применить все фильтры из схемы FilterableFields автоматически

        Args:
            query_builder: Query builder для применения фильтров
            model: SQLAlchemy модель с колонками
            filterable_fields: Схема с фильтрами (наследуется от BaseFilterableFields)

        Returns:
            Query builder с примененными фильтрами
        """
        fields_dict = filterable_fields.get_active_filters()

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

    def _apply_filter_by_type(
        self,
        query_builder: SupportsFiltering,
        column: Any,
        filter_type: type[FilterType],
        field_value: dict[str, Any],
    ) -> SupportsFiltering:
        """
        Применить фильтр определенного типа к query builder

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_type: Тип фильтра (StringFilter, NumberFilter, etc.)
            field_value: Словарь со значениями фильтра

        Returns:
            Query builder с примененным фильтром
        """
        # Создаем экземпляр фильтра из словаря
        filter_instance = filter_type(**field_value)

        # Применяем соответствующий метод в зависимости от типа фильтра
        if filter_type == StringFilter:
            return self.apply_string_filter(query_builder, column, filter_instance)
        elif filter_type == NumberFilter:
            return self.apply_number_filter(query_builder, column, filter_instance)
        elif filter_type == DateTimeFilter:
            return self.apply_datetime_filter(query_builder, column, filter_instance)
        elif filter_type == BooleanFilter:
            return self.apply_boolean_filter(query_builder, column, filter_instance)

        return query_builder

    def _detect_filter_type(
        self, field_value: dict[str, Any]
    ) -> type[StringFilter | NumberFilter | DateTimeFilter | BooleanFilter] | None:
        """
        Определить тип фильтра по структуре данных

        Args:
            field_value: Словарь со значениями фильтра

        Returns:
            Класс фильтра или None, если не удалось определить
        """
        # Проверяем наличие специфичных операций для определения типа

        # Если есть строковые операции - это StringFilter
        if any(key in field_value for key in self._STRING_OPS):
            return StringFilter

        # Если есть операции сравнения - определяем NumberFilter или DateTimeFilter
        if any(key in field_value for key in self._COMPARISON_OPS):
            return self._detect_comparison_filter_type(field_value)

        # Если есть eq, ne, in_, not_in, is_null, is_not_null - определяем по значению
        if any(key in field_value for key in ["eq", "ne", "in_", "not_in"]):
            # Берем первое доступное значение для определения типа
            for key in ["eq", "ne"]:
                if key in field_value and field_value[key] is not None:
                    return self._detect_filter_type_by_value(field_value[key])

            for key in ["in_", "not_in"]:
                if (
                    key in field_value
                    and field_value[key]
                    and len(field_value[key]) > 0
                ):
                    return self._detect_filter_type_by_value(field_value[key][0])

        # Если только is_null или is_not_null - не можем точно определить тип
        # Возвращаем None, фильтр будет обработан базовыми методами
        return None

    @staticmethod
    def _detect_comparison_filter_type(
        field_value: dict[str, Any],
    ) -> type[NumberFilter | DateTimeFilter]:
        """
        Определить тип фильтра для операций сравнения (gt, gte, lt, lte, between)

        Args:
            field_value: Словарь со значениями фильтра

        Returns:
            NumberFilter или DateTimeFilter
        """
        # Проверяем значения операций сравнения
        for key in ["gt", "gte", "lt", "lte"]:
            if key in field_value and field_value[key] is not None:
                value = field_value[key]
                if isinstance(value, (datetime.datetime, datetime.date)):
                    return DateTimeFilter
                return NumberFilter

        # Проверяем between
        if "between" in field_value and field_value["between"] is not None:
            value = field_value["between"]
            if isinstance(value, (tuple, list)) and len(value) > 0:
                if isinstance(value[0], (datetime.datetime, datetime.date)):
                    return DateTimeFilter
                return NumberFilter

        # По умолчанию NumberFilter
        return NumberFilter

    @staticmethod
    def _detect_filter_type_by_value(
        value: Any,
    ) -> type[FilterType] | None:
        """
        Определить тип фильтра по значению

        Args:
            value: Значение для определения типа

        Returns:
            Класс фильтра или None
        """
        if isinstance(value, bool):
            return BooleanFilter
        elif isinstance(value, str):
            return StringFilter
        elif isinstance(value, (int, float)):
            return NumberFilter
        elif isinstance(value, (datetime.datetime, datetime.date)):
            return DateTimeFilter

        return None
