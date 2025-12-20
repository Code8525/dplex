"""Базовая схема для работы с фильтрами, сортировкой и пагинацией"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


from dplex.internal.sort import Sort

# Generic тип для поля сортировки
SortFieldType = TypeVar("SortFieldType")


class DPFilters(BaseModel, Generic[SortFieldType]):
    """
    Базовая схема для фильтруемых полей с поддержкой сортировки и пагинации

    Все схемы фильтров должны наследоваться от этого класса.
    Предоставляет общую конфигурацию и методы для работы с фильтрами,
    сортировкой и пагинацией данных.

    Type Parameters:
        SortFieldType: Тип для полей сортировки (обычно StrEnum с именами полей модели)

    Attributes:
        sort: Параметры сортировки (один объект Sort или список для множественной сортировки)
        limit: Максимальное количество записей для возврата (от 1 до 1000)
        offset: Количество записей для пропуска (от 0 и выше)

    Examples:

        >>> from dplex import StringFilter
        >>> from enum import StrEnum
        >>> from dplex import IntFilter


        >>> class UserSortField(StrEnum):
        ...     NAME = "name"
        ...     EMAIL = "email"
        ...     AGE = "age"
        ...     CREATED_AT = "created_at"
        >>>
        >>> class UserFilterableFields(DPFilters[UserSortField]):
        ...     name: StringFilter | None = None
        ...     email: StringFilter | None = None
        ...     age: IntFilter | None = None
        >>>
        >>> # Создание с фильтрами
        >>> filters = UserFilterableFields(
        ...     name=StringFilter(icontains="john"),
        ...     age=IntFilter(gte=18),
        ...     limit=10,
        ...     offset=0
        ... )


    Note:
        - Все поля фильтров должны быть опциональными (| None)
        - Специальные поля (sort, limit, offset) исключаются из активных фильтров
        - Для изменения фильтров frozen должен быть False в model_config
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

        Исключает специальные поля: sort, limit, offset.
        Возвращает только поля с установленными значениями фильтров.

        Returns:
            Словарь {field_name: filter_instance} с активными фильтрами

        """
        special_fields = {"sort", "limit", "offset"}
        result: dict[str, Any] = {}

        for field_name in type(self).model_fields.keys():
            if field_name in special_fields:
                continue

            field_value = getattr(self, field_name, None)
            if field_value is None:
                continue

            result[field_name] = field_value

        return result

    def has_filters(self) -> bool:
        """
        Проверить, есть ли активные фильтры

        Returns:
            True если есть хотя бы один активный фильтр, иначе False

        """
        return len(self.get_active_filters()) > 0

    def get_filter_fields(self) -> list[str]:
        """
        Получить список имен полей с активными фильтрами

        Returns:
            Список имен полей с активными фильтрами

        """
        return list(self.get_active_filters().keys())

    def get_filter_count(self) -> int:
        """
        Получить количество активных фильтров

        Returns:
            Количество активных фильтров
        """
        return len(self.get_active_filters())

    def get_custom_filters(self, model: type) -> dict[str, Any]:
        """
        Получить кастомные фильтры (поля, которых нет в модели)

        Используется для фильтров, которые не соответствуют полям модели,
        но требуют специальной обработки (например, поиск по нескольким полям).

        Args:
            model: SQLAlchemy модель для проверки наличия полей

        Returns:
            Словарь {field_name: filter_instance} с кастомными фильтрами

        Examples:
            >>> class UserFilterableFields(DPFilters[UserSortField]):
            ...     name: StringFilter | None = None
            ...     query: StringFilter | None = None  # Кастомный фильтр
            >>>
            >>> filters = UserFilterableFields(query=StringFilter(icontains="john"))
            >>> custom = filters.get_custom_filters(User)
            >>> # custom = {"query": StringFilter(icontains="john")}
        """
        active_filters = self.get_active_filters()
        custom_filters: dict[str, Any] = {}

        for field_name, field_value in active_filters.items():
            # Если поля нет в модели - это кастомный фильтр
            if not hasattr(model, field_name):
                custom_filters[field_name] = field_value

        return custom_filters

    def clear_filters(self) -> None:
        """
        Очистить все фильтры (установить все поля фильтров в None)

        Не затрагивает специальные поля: sort, limit, offset.

        Returns:
            None



        Note:
            Работает только если frozen=False в model_config.
            При frozen=True вызовет ValidationError от Pydantic.
        """
        # Поля, которые не нужно очищать
        special_fields = {"sort", "limit", "offset"}

        for field_name in type(self).model_fields.keys():
            if field_name not in special_fields:
                setattr(self, field_name, None)

    def get_filter_summary(self) -> dict[str, int]:
        """
        Получить сводку по количеству операций в каждом активном фильтре

        Подсчитывает количество установленных операций (eq, ne, gt, и т.д.)
        для каждого активного фильтра.

        Returns:
            Словарь {имя_поля: количество_операций}

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
            Словарь с ключами 'limit' и 'offset'
        """
        return {"limit": self.limit, "offset": self.offset}

    def has_pagination(self) -> bool:
        """
        Проверить, установлены ли параметры пагинации

        Returns:
            True если установлен хотя бы один параметр пагинации (limit или offset)
        """
        return self.limit is not None or self.offset is not None

    def has_sort(self) -> bool:
        """
        Проверить, установлены ли параметры сортировки

        Returns:
            True если установлена сортировка, иначе False
        """
        return self.sort is not None

    def __repr__(self) -> str:
        """
        Строковое представление для отладки с информацией об активных фильтрах

        Включает информацию о:
        - Активных фильтрах (список имен полей)
        - Сортировке
        - Пагинации (limit и offset)

        Returns:
            Строка с информацией о классе и активных параметрах
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
        Удобочитаемое строковое представление для пользователя

        Включает:
        - Количество активных фильтров
        - Количество правил сортировки
        - Параметры пагинации

        Returns:
            Строка с человекочитаемым описанием состояния фильтров
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
