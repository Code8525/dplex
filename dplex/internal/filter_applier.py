"""Применение фильтров к query builder для построения SQL запросов"""

import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from dplex.dp_filters import DPFilters

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from dplex.internal.filters import (
    BaseDateTimeFilter,
    BaseNumberFilter,
    BooleanFilter,
    DateFilter,
    DateTimeFilter,
    DecimalFilter,
    EnumFilter,
    FloatFilter,
    IntFilter,
    StringFilter,
    TimeFilter,
    TimestampFilter,
    UUIDFilter,
    WordsFilter,
)
from dplex.internal.types import FilterType


class SupportsFiltering(Protocol):
    """
    Протокол для query builder с поддержкой операций фильтрации

    Определяет интерфейс, который должен реализовать query builder
    для работы с FilterApplier. Включает все базовые операции фильтрации SQL.

    Methods:
        where_eq: Фильтр равенства (column = value)
        where_ne: Фильтр неравенства (column != value)
        where_in: Фильтр вхождения в список (column IN (...))
        where_not_in: Фильтр исключения из списка (column NOT IN (...))
        where_is_null: Проверка на NULL (column IS NULL)
        where_is_not_null: Проверка на NOT NULL (column IS NOT NULL)
        where_gt: Больше чем (column > value)
        where_gte: Больше или равно (column >= value)
        where_lt: Меньше чем (column < value)
        where_lte: Меньше или равно (column <= value)
        where_between: В диапазоне (column BETWEEN start AND end)
        where_like: Соответствие шаблону с учетом регистра (column LIKE pattern)
        where_ilike: Соответствие шаблону без учета регистра (column ILIKE pattern)
    """

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
    """
    Класс для применения фильтров к query builder

    Предоставляет методы для применения различных типов фильтров
    (строковые, числовые, временные и т.д.) к query builder.
    Поддерживает автоматическое определение типа фильтра и применение
    всех фильтров из схемы DPFilters.

    Examples:
        >>> from dplex.internal.filter_applier import FilterApplier
        >>> from dplex import StringFilter, IntFilter
        >>>
        >>> applier = FilterApplier()
        >>>
        >>> # Применение строкового фильтра
        >>> name_filter = StringFilter(icontains="john")
        >>> query = applier.apply_string_filter(query_builder, User.name, name_filter)
        >>>
        >>> # Применение числового фильтра
        >>> age_filter = IntFilter(gte=18, lte=65)
        >>> query = applier.apply_base_number_filter(query_builder, User.age, age_filter)
        >>>
        >>> # Применение всех фильтров из схемы
        >>> filters = UserFilters(name=StringFilter(icontains="john"), age=IntFilter(gte=18))
        >>> query = applier.apply_filters_from_schema(query_builder, User, filters)

    Attributes:
        _STRING_OPS: Набор ключей строковых операций для определения типа
        _COMPARISON_OPS: Набор ключей операций сравнения для определения типа
    """

    # String operation keys for type detection
    _STRING_OPS = frozenset(
        ["contains", "icontains", "starts_with", "ends_with", "like", "ilike"]
    )
    # Comparison operation keys for type detection
    _COMPARISON_OPS = frozenset(["gt", "gte", "lt", "lte", "between", "from_", "to"])

    @staticmethod
    def _apply_common_ops(
        query_builder: SupportsFiltering, column: Any, filter_data: FilterType
    ) -> SupportsFiltering:
        """
        Применить общие операции фильтрации

        Применяет операции, доступные для всех типов фильтров:
        eq, ne, in_, not_in, is_null, is_not_null.

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр фильтра с данными

        Returns:
            Query builder с примененными общими операциями
        """
        if hasattr(filter_data, "eq") and filter_data.eq is not None:
            query_builder = query_builder.where_eq(column, filter_data.eq)
        if hasattr(filter_data, "ne") and filter_data.ne is not None:
            query_builder = query_builder.where_ne(column, filter_data.ne)
        if hasattr(filter_data, "in_") and filter_data.in_ is not None:
            query_builder = query_builder.where_in(column, filter_data.in_)
        if hasattr(filter_data, "not_in") and filter_data.not_in is not None:
            query_builder = query_builder.where_not_in(column, filter_data.not_in)
        if (
            hasattr(filter_data, "is_null")
            and filter_data.is_null is not None
            and filter_data.is_null
        ):
            query_builder = query_builder.where_is_null(column)
        if (
            hasattr(filter_data, "is_not_null")
            and filter_data.is_not_null is not None
            and filter_data.is_not_null
        ):
            query_builder = query_builder.where_is_not_null(column)
        return query_builder

    @staticmethod
    def _apply_comparison_ops(
        query_builder: SupportsFiltering,
        column: Any,
        filter_data: Any,  # BaseNumberFilter or BaseDateTimeFilter
    ) -> SupportsFiltering:
        """
        Применить операции сравнения

        Применяет операции: gt, gte, lt, lte, between.
        Также обрабатывает алиасы from_ и to для временных фильтров.

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр числового или временного фильтра

        Returns:
            Query builder с примененными операциями сравнения
        """
        if hasattr(filter_data, "gt") and filter_data.gt is not None:
            query_builder = query_builder.where_gt(column, filter_data.gt)
        if hasattr(filter_data, "gte") and filter_data.gte is not None:
            query_builder = query_builder.where_gte(column, filter_data.gte)
        if hasattr(filter_data, "lt") and filter_data.lt is not None:
            query_builder = query_builder.where_lt(column, filter_data.lt)
        if hasattr(filter_data, "lte") and filter_data.lte is not None:
            query_builder = query_builder.where_lte(column, filter_data.lte)
        if hasattr(filter_data, "between") and filter_data.between is not None:
            start, end = filter_data.between
            query_builder = query_builder.where_between(column, start, end)
        # Обработка алиасов from_ и to для BaseDateTimeFilter
        if hasattr(filter_data, "from_") and filter_data.from_ is not None:
            query_builder = query_builder.where_gte(column, filter_data.from_)
        if hasattr(filter_data, "to") and filter_data.to is not None:
            query_builder = query_builder.where_lte(column, filter_data.to)
        return query_builder

    @staticmethod
    def _apply_string_ops(
        query_builder: SupportsFiltering, column: Any, filter_data: StringFilter
    ) -> SupportsFiltering:
        """
        Применить строковые операции фильтрации

        Применяет операции: like, ilike, contains, icontains, starts_with, ends_with.
        Автоматически добавляет символы % для паттернов LIKE.

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр строкового фильтра

        Returns:
            Query builder с примененными строковыми операциями
        """
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
        """
        Применить строковый фильтр

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр StringFilter

        Returns:
            Query builder с примененным строковым фильтром
        """
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        query_builder = self._apply_string_ops(query_builder, column, filter_data)
        return query_builder

    def apply_base_number_filter(
        self,
        query_builder: SupportsFiltering,
        column: Any,
        filter_data: BaseNumberFilter,
    ) -> SupportsFiltering:
        """
        Применить базовый числовой фильтр

        Работает для IntFilter, FloatFilter, DecimalFilter и BaseNumberFilter.

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр числового фильтра

        Returns:
            Query builder с примененным числовым фильтром
        """
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        query_builder = self._apply_comparison_ops(query_builder, column, filter_data)
        return query_builder

    def apply_base_datetime_filter(
        self,
        query_builder: SupportsFiltering,
        column: Any,
        filter_data: BaseDateTimeFilter,
    ) -> SupportsFiltering:
        """
        Применить базовый фильтр даты/времени

        Работает для DateTimeFilter, DateFilter, TimeFilter, TimestampFilter
        и BaseDateTimeFilter.

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр фильтра даты/времени

        Returns:
            Query builder с примененным фильтром даты/времени
        """
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        query_builder = self._apply_comparison_ops(query_builder, column, filter_data)
        return query_builder

    def apply_boolean_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: BooleanFilter
    ) -> SupportsFiltering:
        """
        Применить булевый фильтр

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр BooleanFilter

        Returns:
            Query builder с примененным булевым фильтром
        """
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        return query_builder

    def apply_enum_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: EnumFilter
    ) -> SupportsFiltering:
        """
        Применить enum фильтр

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр EnumFilter

        Returns:
            Query builder с примененным enum фильтром
        """
        filter_data = self._coerce_enum_filter_values(column, filter_data)
        return self._apply_common_ops(query_builder, column, filter_data)

    @staticmethod
    def _get_sa_enum_type(column: InstrumentedAttribute | Any) -> sa.Enum | None:
        col_type = getattr(column, "type", None)
        return col_type if isinstance(col_type, sa.Enum) else None

    @staticmethod
    def _coerce_single_enum_value(sa_enum: sa.Enum, value: Any) -> Any:
        enum_class = getattr(sa_enum, "enum_class", None)

        if isinstance(value, Enum):
            if enum_class and isinstance(value, enum_class):
                return value
            str_val = getattr(value, "value", str(value))
            if not enum_class and sa_enum.enums and str_val in sa_enum.enums:
                return str_val
            raise ValueError(f"Enum value '{value}' is not compatible with column enum")

        if isinstance(value, str):
            if enum_class:
                try:
                    return enum_class(value)  # по .value
                except Exception:
                    try:
                        return enum_class[value]  # по .name
                    except Exception:
                        pass
                raise ValueError(
                    f"Invalid enum literal '{value}' for {enum_class.__name__}"
                )
            if sa_enum.enums and value in sa_enum.enums:
                return value
            raise ValueError(f"Invalid enum literal '{value}' for DB enum")

        raise ValueError(f"Unsupported enum filter value type: {type(value).__name__}")

    @classmethod
    def _coerce_enum_filter_values(cls, column: Any, filt: EnumFilter) -> EnumFilter:
        sa_enum = cls._get_sa_enum_type(column)
        if not sa_enum:
            return filt

        def map_list(lst):
            return (
                None
                if lst is None
                else [cls._coerce_single_enum_value(sa_enum, v) for v in lst]
            )

        if getattr(filt, "eq", None) is not None:
            filt.eq = cls._coerce_single_enum_value(sa_enum, filt.eq)
        if getattr(filt, "ne", None) is not None:
            filt.ne = cls._coerce_single_enum_value(sa_enum, filt.ne)
        if getattr(filt, "in_", None) is not None:
            filt.in_ = map_list(filt.in_)
        if getattr(filt, "not_in", None) is not None:
            filt.not_in = map_list(filt.not_in)
        return filt

    def apply_uuid_filter(
        self, query_builder: SupportsFiltering, column: Any, filter_data: UUIDFilter
    ) -> SupportsFiltering:
        """
        Применить UUID фильтр

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_data: Экземпляр UUIDFilter

        Returns:
            Query builder с примененным UUID фильтром
        """
        query_builder = self._apply_common_ops(query_builder, column, filter_data)
        return query_builder

    def apply_words_filter(
        self,
        query_builder: SupportsFiltering,
        filter_data: WordsFilter,
    ) -> SupportsFiltering:
        """
        Применить фильтр слов к нескольким колонкам

        Ищет каждое слово из filter_data.words в указанных колонках.
        Для каждого слова создается условие OR (слово должно быть найдено хотя бы в одной колонке).
        Все слова объединяются через AND (все слова должны быть найдены).

        Если filter_data.text или filter_data.columns равны None, фильтр не применяется.

        Args:
            query_builder: Query builder для применения фильтров
            filter_data: Экземпляр WordsFilter с указанными колонками

        Returns:
            Query builder с примененным фильтром слов (или без изменений, если фильтр не активен)

        Examples:
            >>> from sqlalchemy import and_, or_
            >>> words_filter = WordsFilter("john developer", columns=[User.name, User.email])
            >>> query = applier.apply_words_filter(query_builder, words_filter)
            >>>
            >>> # Фильтр не будет применен, если text или columns равны None
            >>> inactive_filter = WordsFilter(None, None)
            >>> query = applier.apply_words_filter(query_builder, inactive_filter)  # вернет query без изменений
        """
        from sqlalchemy import and_, or_

        search_columns = filter_data.columns

        # Если columns равны None или пустые, фильтр не применяется
        if search_columns is None or not search_columns:
            return query_builder

        words = filter_data.words
        # Если words пустые (text был None или пустой), фильтр не применяется
        if not words:
            return query_builder

        # Для каждого слова создаем условие: слово должно быть найдено хотя бы в одной колонке (OR)
        word_conditions = []
        for word in words:
            column_conditions = [col.ilike(f"%{word}%") for col in search_columns]
            word_conditions.append(or_(*column_conditions))

        # Все слова должны быть найдены (AND между словами)
        if word_conditions:
            query_builder = query_builder.where(and_(*word_conditions))

        return query_builder

    def apply_filters_from_schema(
        self,
        query_builder: SupportsFiltering,
        model: type,
        filterable_fields: DPFilters,
    ) -> SupportsFiltering:
        """
        Применить все фильтры из схемы автоматически

        Извлекает активные фильтры из DPFilters и применяет их к query builder.
        Автоматически определяет тип каждого фильтра и применяет соответствующий метод.
        Пропускает поля, отсутствующие в модели, кроме WordsFilter (который обрабатывается отдельно).

        Args:
            query_builder: Query builder для применения фильтров
            model: SQLAlchemy модель с колонками
            filterable_fields: Схема с фильтрами (наследуется от DPFilters)

        Returns:
            Query builder с примененными фильтрами

        Examples:
            >>> from dplex.internal.filters import StringFilter, IntFilter
            >>> from dplex.dp_filters import DPFilters
            >>>
            >>> class UserFilters(DPFilters):
            ...     name: StringFilter | None = None
            ...     age: IntFilter | None = None
            >>>
            >>> filters = UserFilters(
            ...     name=StringFilter(icontains="john"),
            ...     age=IntFilter(gte=18)
            ... )
            >>> applier = FilterApplier()
            >>> query = applier.apply_filters_from_schema(query_builder, User, filters)
        """
        # Получаем активные фильтры как словарь {field_name: filter_instance}
        fields_dict = filterable_fields.get_active_filters()

        for field_name, field_value in fields_dict.items():
            # Пропускаем None
            if field_value is None:
                continue

            # Обрабатываем WordsFilter отдельно (может быть кастомным фильтром)
            if isinstance(field_value, WordsFilter):
                # WordsFilter теперь всегда имеет колонки (обязательный параметр)
                query_builder = self.apply_words_filter(query_builder, field_value)
                continue

            # Пропускаем поля, отсутствующие в модели
            if not hasattr(model, field_name):
                continue

            column = getattr(model, field_name)

            # Применяем фильтры по типам (только экземпляры классов)
            if isinstance(field_value, StringFilter):
                query_builder = self.apply_string_filter(
                    query_builder, column, field_value
                )
            elif isinstance(field_value, BooleanFilter):
                query_builder = self.apply_boolean_filter(
                    query_builder, column, field_value
                )
            elif isinstance(field_value, UUIDFilter):
                query_builder = self.apply_uuid_filter(
                    query_builder, column, field_value
                )
            elif isinstance(field_value, (IntFilter, FloatFilter, DecimalFilter)):
                query_builder = self.apply_base_number_filter(
                    query_builder, column, field_value
                )
            elif isinstance(
                field_value, (DateTimeFilter, DateFilter, TimeFilter, TimestampFilter)
            ):
                query_builder = self.apply_base_datetime_filter(
                    query_builder, column, field_value
                )
            elif isinstance(field_value, EnumFilter):
                query_builder = self.apply_enum_filter(
                    query_builder, column, field_value
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

        Создает экземпляр фильтра из словаря и применяет соответствующий метод.

        Args:
            query_builder: Query builder для применения фильтров
            column: Колонка модели для фильтрации
            filter_type: Тип фильтра (StringFilter, IntFilter и т.д.)
            field_value: Словарь со значениями фильтра

        Returns:
            Query builder с примененным фильтром
        """
        # Создаем экземпляр фильтра из словаря
        filter_instance = filter_type(**field_value)

        # Применяем соответствующий метод в зависимости от типа фильтра
        # Строковые фильтры
        if filter_type == StringFilter:
            return self.apply_string_filter(query_builder, column, filter_instance)
        # Булевые фильтры
        elif filter_type == BooleanFilter:
            return self.apply_boolean_filter(query_builder, column, filter_instance)
        # Числовые фильтры (используем базовый метод для всех)
        elif filter_type in (IntFilter, FloatFilter, DecimalFilter, BaseNumberFilter):
            return self.apply_base_number_filter(query_builder, column, filter_instance)
        # Фильтры даты/времени (используем базовый метод для всех)
        elif filter_type in (
            DateTimeFilter,
            DateFilter,
            TimeFilter,
            TimestampFilter,
            BaseDateTimeFilter,
        ):
            return self.apply_base_datetime_filter(
                query_builder, column, filter_instance
            )
        # Enum фильтры
        elif filter_type == EnumFilter:
            return self.apply_enum_filter(query_builder, column, filter_instance)
        # UUID фильтры
        elif filter_type == UUIDFilter:
            return self.apply_uuid_filter(query_builder, column, filter_instance)

        return query_builder

    def _detect_filter_type(
        self, field_value: dict[str, Any]
    ) -> type[FilterType] | None:
        """
        Определить тип фильтра по структуре данных

        Анализирует ключи и значения словаря для определения
        подходящего типа фильтра.

        Args:
            field_value: Словарь со значениями фильтра

        Returns:
            Класс фильтра или None, если не удалось определить

        Notes:
            Приоритет определения:
            1. Строковые операции (contains, icontains и т.д.)
            2. Операции сравнения (gt, gte, lt, lte, between)
            3. Базовые операции (eq, ne, in_, not_in) - по типу значения
        """
        # Проверяем наличие специфичных операций для определения типа
        # Если есть строковые операции - это StringFilter
        if any(key in field_value for key in self._STRING_OPS):
            return StringFilter

        # Если есть операции сравнения - определяем числовой или временной фильтр
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
    ) -> type[FilterType]:
        """
        Определить тип фильтра для операций сравнения

        Анализирует значения операций gt, gte, lt, lte, between, from_, to
        для определения конкретного типа фильтра.

        Args:
            field_value: Словарь со значениями фильтра

        Returns:
            Соответствующий класс фильтра

        Notes:
            Порядок проверки типов:
            1. datetime.datetime → DateTimeFilter
            2. datetime.date → DateFilter
            3. datetime.time → TimeFilter
            4. Decimal → DecimalFilter
            5. float → FloatFilter
            6. int → IntFilter или TimestampFilter (если есть from_/to)
        """
        # Проверяем значения операций сравнения
        for key in ["gt", "gte", "lt", "lte", "from_", "to"]:
            if key in field_value and field_value[key] is not None:
                value = field_value[key]
                # Проверяем тип значения
                if isinstance(value, datetime.datetime):
                    return DateTimeFilter
                elif isinstance(value, datetime.date):
                    return DateFilter
                elif isinstance(value, datetime.time):
                    return TimeFilter
                elif isinstance(value, Decimal):
                    return DecimalFilter
                elif isinstance(value, float):
                    return FloatFilter
                elif isinstance(value, int):
                    # Может быть IntFilter или TimestampFilter
                    # Если есть from_/to алиасы - скорее всего BaseDateTimeFilter
                    if "from_" in field_value or "to" in field_value:
                        return TimestampFilter
                    return IntFilter

        # Проверяем between
        if "between" in field_value and field_value["between"] is not None:
            value = field_value["between"]
            if isinstance(value, (tuple, list)) and len(value) > 0:
                first_val = value[0]
                if isinstance(first_val, datetime.datetime):
                    return DateTimeFilter
                elif isinstance(first_val, datetime.date):
                    return DateFilter
                elif isinstance(first_val, datetime.time):
                    return TimeFilter
                elif isinstance(first_val, Decimal):
                    return DecimalFilter
                elif isinstance(first_val, float):
                    return FloatFilter
                elif isinstance(first_val, int):
                    return IntFilter

        # По умолчанию IntFilter
        return IntFilter

    @staticmethod
    def _detect_filter_type_by_value(
        value: Any,
    ) -> type[FilterType] | None:
        """
        Определить тип фильтра по значению

        Проверяет тип значения для определения подходящего класса фильтра.

        Args:
            value: Значение для определения типа

        Returns:
            Класс фильтра или None если тип не распознан

        Notes:
            ВАЖНО: порядок проверок имеет значение!
            - bool проверяется до int (bool является подклассом int)
            - datetime проверяется до date (datetime является подклассом date)
            - Decimal проверяется до float/int
        """
        # Важно: порядок проверок имеет значение!
        # bool является подклассом int, поэтому проверяем его первым
        if isinstance(value, bool):
            return BooleanFilter
        # Проверяем Enum
        elif isinstance(value, Enum):
            return EnumFilter
        # Проверяем UUID
        elif isinstance(value, UUID):
            return UUIDFilter
        # Проверяем datetime (до date, т.к. datetime - подкласс date)
        elif isinstance(value, datetime.datetime):
            return DateTimeFilter
        # Проверяем date
        elif isinstance(value, datetime.date):
            return DateFilter
        # Проверяем time
        elif isinstance(value, datetime.time):
            return TimeFilter
        # Проверяем Decimal (до float/int)
        elif isinstance(value, Decimal):
            return DecimalFilter
        # Проверяем float (до int, т.к. порядок важен)
        elif isinstance(value, float):
            return FloatFilter
        # Проверяем int
        elif isinstance(value, int):
            return IntFilter
        # Проверяем str
        elif isinstance(value, str):
            return StringFilter

        return None
