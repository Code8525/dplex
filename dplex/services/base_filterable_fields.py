from typing import Any
from pydantic import BaseModel, ConfigDict


class BaseFilterableFields(BaseModel):
    """
    Базовая схема для фильтруемых полей

    Все схемы фильтров должны наследоваться от этого класса.
    Предоставляет общую конфигурацию и методы для работы с фильтрами.

    Example:
        ```python
        from src.dplex.services import BaseFilterableFields
        from src.dplex.services.filters import StringFilter, IntFilter

        class UserFilterableFields(BaseFilterableFields):
            name: StringFilter | None = None
            email: StringFilter | None = None
            age: IntFilter | None = None
        ```
    """

    model_config = ConfigDict(
        # Разрешаем произвольные типы для фильтров
        arbitrary_types_allowed=True,
        # Дополнительные поля запрещены
        extra="forbid",
        # Запрещаем изменение после создания (immutable)
        frozen=False,
    )

    def get_active_filters(self) -> dict[str, Any]:
        """
        Получить словарь только с активными (не None) фильтрами

        Returns:
            Словарь с активными фильтрами в виде dict[str, dict[str, Any]]

        Example:
            >>> filters = UserFilterableFields(name=StringFilter(eq="John"))
            >>> filters.get_active_filters()
            {'name': {'eq': 'John', 'ne': None, ...}}
        """
        result: dict[str, Any] = {}

        for field_name, field_value in self.model_dump(exclude_none=True).items():
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

        Example:
            >>> filters = UserFilterableFields(name=StringFilter(eq="John"))
            >>> filters.has_filters()
            True
            >>> filters.clear_filters()
            >>> filters.has_filters()
            False
        """
        for field_name in self.model_fields.keys():
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

    def __repr__(self) -> str:
        """
        Строковое представление с информацией об активных фильтрах

        Returns:
            Строка с информацией о классе и активных фильтрах
        """
        active = self.get_filter_fields()
        if active:
            fields_str = ", ".join(active)
            return f"{self.__class__.__name__}(active_filters=[{fields_str}])"
        return f"{self.__class__.__name__}(no_active_filters)"

    def __str__(self) -> str:
        """
        Удобочитаемое строковое представление

        Returns:
            Строка с количеством активных фильтров
        """
        count = self.get_filter_count()
        if count == 0:
            return f"{self.__class__.__name__}: No active filters"
        elif count == 1:
            return f"{self.__class__.__name__}: 1 active filter"
        else:
            return f"{self.__class__.__name__}: {count} active filters"
