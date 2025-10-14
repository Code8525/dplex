from typing import Any, TypeVar, Generic
from pydantic import BaseModel, ConfigDict, Field

from dplex.services.sort import Sort

# Generic тип для поля сортировки
SortFieldType = TypeVar("SortFieldType")


class DPFilters(BaseModel, Generic[SortFieldType]):
    """
    Базовая схема для фильтруемых полей

    Все схемы фильтров должны наследоваться от этого класса.
    Предоставляет общую конфигурацию и методы для работы с фильтрами.

    Attributes:
        sort: Параметры сортировки (один объект Sort или список)
        limit: Максимальное количество записей для возврата
        offset: Количество записей для пропуска

    Example:
        ```python
        from enum import StrEnum
        from dplex.services import DPFilters
        from dplex.services.filters import StringFilter, IntFilter

        class UserSortField(StrEnum):
            NAME = "name"
            EMAIL = "email"
            AGE = "age"
            CREATED_AT = "created_at"

        class UserFilterableFields(DPFilters[UserSortField]):
            name: StringFilter | None = None
            email: StringFilter | None = None
            age: IntFilter | None = None
        ```
    """

    # Сортировка (ОБЯЗАТЕЛЬНО назвать 'sort')
    sort: list[Sort[SortFieldType]] | Sort[SortFieldType] | None = Field(
        default=None,
        description="Параметры сортировки. Может быть одним объектом Sort или списком для множественной сортировки",
    )

    # Пагинация
    limit: int | None = Field(
        default=None,
        ge=1,
        le=1000,
        description="Максимальное количество записей для возврата (от 1 до 1000)",
    )

    offset: int | None = Field(
        default=None, ge=0, description="Количество записей для пропуска (от 0 и выше)"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=False,
    )

    def get_active_filters(self) -> dict[str, Any]:
        """
        Получить словарь только с активными (не None) фильтрами

        Исключает специальные поля: sort, limit, offset

        Returns:
            Словарь с активными фильтрами в виде dict[str, dict[str, Any]]

        Example:
            >>> filters = UserFilterableFields(name=StringFilter(eq="John"))
            >>> filters.get_active_filters()
            {'name': {'eq': 'John', 'ne': None, ...}}
        """
        # Поля, которые не являются фильтрами
        special_fields = {"sort", "limit", "offset"}

        result: dict[str, Any] = {}
        for field_name, field_value in self.model_dump(exclude_none=True).items():
            # Пропускаем специальные поля
            if field_name in special_fields:
                continue

            # Пропускаем None значения
            if field_value is None:
                continue

            # Если это словарь (сериализованный фильтр)
            if isinstance(field_value, dict):
                # Удаляем все None значения из словаря фильтра
                cleaned_filter = {k: v for k, v in field_value.items() if v is not None}
                # Добавляем только если остались какие-то значения
                if cleaned_filter:
                    result[field_name] = cleaned_filter
            else:
                # Для других типов добавляем как есть
                result[field_name] = field_value

        return result

    def has_filters(self) -> bool:
        """
        Проверить, есть ли активные фильтры

        Returns:
            True если есть хотя бы один активный фильтр

        Example:
            >>> filters = UserFilterableFields()
            >>> filters.has_filters()
            False
            >>> filters = UserFilterableFields(name=StringFilter(eq="John"))
            >>> filters.has_filters()
            True
        """
        return len(self.get_active_filters()) > 0

    def get_filter_fields(self) -> list[str]:
        """
        Получить список имен полей с активными фильтрами

        Returns:
            Список имен полей с активными фильтрами

        Example:
            >>> filters = UserFilterableFields(
            ...     name=StringFilter(eq="John"),
            ...     age=IntFilter(gte=18)
            ... )
            >>> filters.get_filter_fields()
            ['name', 'age']
        """
        return list(self.get_active_filters().keys())

    def get_filter_count(self) -> int:
        """
        Получить количество активных фильтров

        Returns:
            Количество активных фильтров

        Example:
            >>> filters = UserFilterableFields(
            ...     name=StringFilter(eq="John"),
            ...     age=IntFilter(gte=18)
            ... )
            >>> filters.get_filter_count()
            2
        """
        return len(self.get_active_filters())

    def clear_filters(self) -> None:
        """
        Очистить все фильтры (установить все поля в None)

        Note:
            Работает только если frozen=False в model_config
            Не затрагивает поля sort, limit, offset

        Example:
            >>> filters = UserFilterableFields(name=StringFilter(eq="John"))
            >>> filters.has_filters()
            True
            >>> filters.clear_filters()
            >>> filters.has_filters()
            False
        """
        # Поля, которые не нужно очищать
        special_fields = {"sort", "limit", "offset"}

        for field_name in self.model_fields.keys():
            if field_name not in special_fields:
                setattr(self, field_name, None)

    def get_filter_summary(self) -> dict[str, int]:
        """
        Получить сводку по количеству операций в каждом фильтре

        Returns:
            Словарь {имя_поля: количество_операций}

        Example:
            >>> filters = UserFilterableFields(
            ...     name=StringFilter(eq="John", icontains="Doe"),
            ...     age=IntFilter(gte=18, lte=65)
            ... )
            >>> filters.get_filter_summary()
            {'name': 2, 'age': 2}
        """
        summary: dict[str, int] = {}
        active_filters = self.get_active_filters()

        for field_name, field_value in active_filters.items():
            if isinstance(field_value, dict):
                # Считаем количество непустых операций
                summary[field_name] = len(
                    [v for v in field_value.values() if v is not None]
                )
            else:
                summary[field_name] = 1

        return summary

    def get_pagination_info(self) -> dict[str, int | None]:
        """
        Получить информацию о пагинации

        Returns:
            Словарь с limit и offset

        Example:
            >>> filters = UserFilterableFields(limit=10, offset=20)
            >>> filters.get_pagination_info()
            {'limit': 10, 'offset': 20}
        """
        return {"limit": self.limit, "offset": self.offset}

    def has_pagination(self) -> bool:
        """
        Проверить, установлены ли параметры пагинации

        Returns:
            True если установлен хотя бы один параметр пагинации

        Example:
            >>> filters = UserFilterableFields(limit=10)
            >>> filters.has_pagination()
            True
        """
        return self.limit is not None or self.offset is not None

    def has_sort(self) -> bool:
        """
        Проверить, установлены ли параметры сортировки

        Returns:
            True если установлена сортировка

        Example:
            >>> filters = UserFilterableFields(sort=Sort(by=UserSortField.NAME))
            >>> filters.has_sort()
            True
        """
        return self.sort is not None

    def __repr__(self) -> str:
        """
        Строковое представление с информацией об активных фильтрах

        Returns:
            Строка с информацией о классе и активных фильтрах
        """
        active = self.get_filter_fields()
        parts = []

        if active:
            fields_str = ", ".join(active)
            parts.append(f"filters=[{fields_str}]")

        if self.has_sort():
            parts.append(f"sort={self.sort}")

        if self.has_pagination():
            pag_parts = []
            if self.limit is not None:
                pag_parts.append(f"limit={self.limit}")
            if self.offset is not None:
                pag_parts.append(f"offset={self.offset}")
            parts.append(", ".join(pag_parts))

        if parts:
            return f"{self.__class__.__name__}({', '.join(parts)})"

        return f"{self.__class__.__name__}(no_active_filters)"

    def __str__(self) -> str:
        """
        Удобочитаемое строковое представление

        Returns:
            Строка с количеством активных фильтров и информацией о пагинации
        """
        count = self.get_filter_count()
        parts = []

        if count == 0:
            parts.append("No active filters")
        elif count == 1:
            parts.append("1 active filter")
        else:
            parts.append(f"{count} active filters")

        if self.has_sort():
            sort_count = len(self.sort) if isinstance(self.sort, list) else 1
            parts.append(f"{sort_count} sort rule(s)")

        if self.has_pagination():
            pag_info = []
            if self.limit is not None:
                pag_info.append(f"limit={self.limit}")
            if self.offset is not None:
                pag_info.append(f"offset={self.offset}")
            parts.append(f"pagination({', '.join(pag_info)})")

        return f"{self.__class__.__name__}: {', '.join(parts)}"
