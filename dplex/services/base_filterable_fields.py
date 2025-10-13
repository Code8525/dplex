from typing import Any
from pydantic import BaseModel, ConfigDict


class BaseFilterableFields(BaseModel):
    """
    Базовая схема для фильтруемых полей

    Все схемы фильтров должны наследоваться от этого класса.
    Предоставляет общую конфигурацию и методы для работы с фильтрами.

    Example:
        ```python
        from dplex.services import BaseFilterableFields
        from dplex.services.filters import StringFilter, NumberFilter

        class UserFilterableFields(BaseFilterableFields):
            name: StringFilter | None = None
            email: StringFilter | None = None
            age: NumberFilter[int] | None = None
        ```
    """

    model_config = ConfigDict(
        # Разрешаем произвольные типы для фильтров
        arbitrary_types_allowed=True,
        # Дополнительные поля запрещены
        extra="forbid",
    )

    def get_active_filters(self) -> dict[str, Any]:
        """
        Получить словарь только с активными (не None) фильтрами

        Returns:
            Словарь с активными фильтрами
        """
        return self.model_dump(exclude_none=True)

    def has_filters(self) -> bool:
        """
        Проверить, есть ли активные фильтры

        Returns:
            True если есть хотя бы один активный фильтр
        """
        return len(self.get_active_filters()) > 0

    def get_filter_fields(self) -> list[str]:
        """
        Получить список имен полей с активными фильтрами

        Returns:
            Список имен полей
        """
        return list(self.get_active_filters().keys())
