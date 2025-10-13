from typing import Any, Generic
from sqlalchemy import ColumnElement, asc, desc, nullsfirst, nullslast
from sqlalchemy.orm import InstrumentedAttribute

from src.dplex.repositories.repository import DPRepo
from src.dplex.services.sort import Sort, SortDirection, NullsPlacement
from src.dplex.types import ModelType, SortFieldType


class QueryBuilder(Generic[ModelType]):
    """Query Builder с улучшенной типизацией и поддержкой Sort"""

    def __init__(self, repo: DPRepo[ModelType, Any], model: type[ModelType]) -> None:
        self.repo = repo
        self.model = model
        self.filters: list[ColumnElement[bool]] = []
        self.limit_value: int | None = None
        self.offset_value: int | None = None
        self.order_by_clauses: list[Any] = []

    def where(self, condition: ColumnElement[bool]) -> "QueryBuilder[ModelType]":
        """WHERE condition (принимает готовое условие)"""
        self.filters.append(condition)
        return self

    def where_eq(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """WHERE column = value"""
        condition: ColumnElement[bool] = column == value
        return self.where(condition)

    def where_ne(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """WHERE column != value"""
        condition: ColumnElement[bool] = column != value
        return self.where(condition)

    def where_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[ModelType]":
        """WHERE column IN (values)"""
        if not values:
            # Если список пустой, добавляем условие которое всегда false
            condition: ColumnElement[bool] = column.in_([])
        else:
            condition = column.in_(values)
        return self.where(condition)

    def where_not_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[ModelType]":
        """WHERE column NOT IN (values)"""
        if not values:
            # Если список пустой, условие всегда true - не добавляем фильтр
            return self
        condition: ColumnElement[bool] = ~column.in_(values)
        return self.where(condition)

    def where_is_null(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """WHERE column IS NULL"""
        condition: ColumnElement[bool] = column.is_(None)
        return self.where(condition)

    def where_is_not_null(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """WHERE column IS NOT NULL"""
        condition: ColumnElement[bool] = column.isnot(None)
        return self.where(condition)

    def where_like(
        self, column: InstrumentedAttribute[Any], pattern: str
    ) -> "QueryBuilder[ModelType]":
        """WHERE column LIKE pattern"""
        condition: ColumnElement[bool] = column.like(pattern)
        return self.where(condition)

    def where_ilike(
        self, column: InstrumentedAttribute[Any], pattern: str
    ) -> "QueryBuilder[ModelType]":
        """WHERE column ILIKE pattern (case-insensitive)"""
        condition: ColumnElement[bool] = column.ilike(pattern)
        return self.where(condition)

    def where_between(
        self, column: InstrumentedAttribute[Any], start: Any, end: Any
    ) -> "QueryBuilder[ModelType]":
        """WHERE column BETWEEN start AND end"""
        condition: ColumnElement[bool] = column.between(start, end)
        return self.where(condition)

    def where_gt(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """WHERE column > value"""
        condition: ColumnElement[bool] = column > value
        return self.where(condition)

    def where_gte(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """WHERE column >= value"""
        condition: ColumnElement[bool] = column >= value
        return self.where(condition)

    def where_lt(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """WHERE column < value"""
        condition: ColumnElement[bool] = column < value
        return self.where(condition)

    def where_lte(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """WHERE column <= value"""
        condition: ColumnElement[bool] = column <= value
        return self.where(condition)

    def limit(self, limit: int) -> "QueryBuilder[ModelType]":
        """LIMIT записей"""
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        self.limit_value = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder[ModelType]":
        """OFFSET записей"""
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        self.offset_value = offset
        return self

    def paginate(self, page: int, per_page: int) -> "QueryBuilder[ModelType]":
        """Пагинация (page начинается с 1)"""
        if page < 1:
            raise ValueError("Page must be >= 1")
        if per_page < 1:
            raise ValueError("Per page must be >= 1")
        self.limit_value = per_page
        self.offset_value = (page - 1) * per_page
        return self

    def order_by(
        self, column: InstrumentedAttribute[Any], desc_order: bool = False
    ) -> "QueryBuilder[ModelType]":
        """
        ORDER BY column

        Args:
            column: Колонка для сортировки
            desc_order: True для DESC, False для ASC (по умолчанию)
        """
        order_clause = column.desc() if desc_order else column.asc()
        self.order_by_clauses.append(order_clause)
        return self

    def order_by_desc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """ORDER BY column DESC"""
        return self.order_by(column, desc_order=True)

    def order_by_asc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """ORDER BY column ASC"""
        return self.order_by(column, desc_order=False)

    def order_by_with_nulls(
        self,
        column: InstrumentedAttribute[Any],
        desc_order: bool = False,
        nulls_placement: NullsPlacement | None = None,
    ) -> "QueryBuilder[ModelType]":
        """
        ORDER BY column с управлением NULL значениями

        Args:
            column: Колонка для сортировки
            desc_order: True для DESC, False для ASC
            nulls_placement: Размещение NULL (FIRST или LAST)

        Example:
            qb.order_by_with_nulls(
                User.created_at,
                desc_order=True,
                nulls_placement=NullsPlacement.LAST
            )
        """
        # Создаем базовую сортировку
        if desc_order:
            order_clause = desc(column)
        else:
            order_clause = asc(column)

        # Применяем nulls placement если указан
        if nulls_placement == NullsPlacement.FIRST:
            order_clause = nullsfirst(order_clause)
        elif nulls_placement == NullsPlacement.LAST:
            order_clause = nullslast(order_clause)

        self.order_by_clauses.append(order_clause)
        return self

    def apply_sort(
        self, sort_item: Sort[Any], column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """
        Применить Sort объект к query builder

        Args:
            sort_item: Объект Sort с параметрами сортировки
            column: Колонка модели для сортировки

        Example:
            sort = Sort(
                field=UserSortField.CREATED_AT,
                direction=SortDirection.DESC,
                nulls=NullsPlacement.LAST
            )
            qb.apply_sort(sort, User.created_at)
        """
        desc_order = sort_item.direction == SortDirection.DESC
        return self.order_by_with_nulls(column, desc_order, sort_item.nulls)

    def apply_sorts(
        self,
        sort_list: list[Sort[Any]],
        column_mapper: dict[Any, InstrumentedAttribute[Any]],
    ) -> "QueryBuilder[ModelType]":
        """
        Применить список Sort объектов к query builder

        Args:
            sort_list: Список объектов Sort
            column_mapper: Словарь для маппинга field -> column
                          {SortField.USERNAME: User.username, ...}

        Example:
            sorts = [
                Sort(field=UserSortField.CREATED_AT, direction=SortDirection.DESC),
                Sort(field=UserSortField.USERNAME, direction=SortDirection.ASC)
            ]
            mapper = {
                UserSortField.CREATED_AT: User.created_at,
                UserSortField.USERNAME: User.username
            }
            qb.apply_sorts(sorts, mapper)
        """
        for sort_item in sort_list:
            column = column_mapper.get(sort_item.field)
            if column is None:
                raise ValueError(
                    f"Column mapping not found for field: {sort_item.field}"
                )
            self.apply_sort(sort_item, column)
        return self

    def clear_order(self) -> "QueryBuilder[ModelType]":
        """Очистить сортировку"""
        self.order_by_clauses = []
        return self

    async def find_all(self) -> list[ModelType]:
        """Выполнить запрос и вернуть все результаты"""
        return await self.repo.execute_typed_query(self)

    async def find_one(self) -> ModelType | None:
        """Выполнить запрос и вернуть первый результат"""
        self.limit_value = 1
        results = await self.find_all()
        return results[0] if results else None

    async def find_first(self) -> ModelType:
        """Выполнить запрос и вернуть первый результат, иначе ошибка"""
        result = await self.find_one()
        if result is None:
            raise ValueError(f"No {self.model.__name__} found matching criteria")
        return result

    async def count(self) -> int:
        """Подсчитать количество записей"""
        return await self.repo.execute_typed_count(self)

    async def exists(self) -> bool:
        """Проверить существование записей"""
        count = await self.count()
        return count > 0
