from typing import Any, Generic, TypeVar
from sqlalchemy import select, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

from dataplex import BaseRepository

ModelSchema = TypeVar("ModelSchema", bound=DeclarativeBase)


class QueryBuilder(Generic[ModelSchema]):
    """Query Builder с улучшенной типизацией"""

    def __init__(
        self, repo: BaseRepository[ModelSchema, Any], model: type[ModelSchema]
    ) -> None:
        self.repo = repo
        self.model = model
        self.filters: list[ColumnElement[bool]] = []
        self.limit_value: int | None = None
        self.offset_value: int | None = None
        self.order_by_clauses: list[Any] = []

    def where(self, condition: ColumnElement[bool]) -> "QueryBuilder[ModelSchema]":
        """WHERE condition (принимает готовое условие)"""
        self.filters.append(condition)
        return self

    def where_eq(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column = value"""
        condition: ColumnElement[bool] = column == value
        return self.where(condition)

    def where_ne(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column != value"""
        condition: ColumnElement[bool] = column != value
        return self.where(condition)

    def where_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column IN (values)"""
        if not values:
            # Если список пустой, добавляем условие которое всегда false
            condition: ColumnElement[bool] = column.in_([])
        else:
            condition = column.in_(values)
        return self.where(condition)

    def where_not_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column NOT IN (values)"""
        if not values:
            # Если список пустой, условие всегда true - не добавляем фильтр
            return self
        condition: ColumnElement[bool] = ~column.in_(values)
        return self.where(condition)

    def where_is_null(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column IS NULL"""
        condition: ColumnElement[bool] = column.is_(None)
        return self.where(condition)

    def where_is_not_null(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column IS NOT NULL"""
        condition: ColumnElement[bool] = column.isnot(None)
        return self.where(condition)

    def where_like(
        self, column: InstrumentedAttribute[Any], pattern: str
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column LIKE pattern"""
        condition: ColumnElement[bool] = column.like(pattern)
        return self.where(condition)

    def where_ilike(
        self, column: InstrumentedAttribute[Any], pattern: str
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column ILIKE pattern (case-insensitive)"""
        condition: ColumnElement[bool] = column.ilike(pattern)
        return self.where(condition)

    def where_between(
        self, column: InstrumentedAttribute[Any], start: Any, end: Any
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column BETWEEN start AND end"""
        condition: ColumnElement[bool] = column.between(start, end)
        return self.where(condition)

    def where_gt(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column > value"""
        condition: ColumnElement[bool] = column > value
        return self.where(condition)

    def where_gte(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column >= value"""
        condition: ColumnElement[bool] = column >= value
        return self.where(condition)

    def where_lt(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column < value"""
        condition: ColumnElement[bool] = column < value
        return self.where(condition)

    def where_lte(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelSchema]":
        """WHERE column <= value"""
        condition: ColumnElement[bool] = column <= value
        return self.where(condition)

    def limit(self, limit: int) -> "QueryBuilder[ModelSchema]":
        """LIMIT записей"""
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        self.limit_value = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder[ModelSchema]":
        """OFFSET записей"""
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        self.offset_value = offset
        return self

    def paginate(self, page: int, per_page: int) -> "QueryBuilder[ModelSchema]":
        """Пагинация (page начинается с 1)"""
        if page < 1:
            raise ValueError("Page must be >= 1")
        if per_page < 1:
            raise ValueError("Per page must be >= 1")

        self.limit_value = per_page
        self.offset_value = (page - 1) * per_page
        return self

    def order_by(
        self, column: InstrumentedAttribute[Any], desc: bool = False
    ) -> "QueryBuilder[ModelSchema]":
        """ORDER BY column"""
        order_clause = column.desc() if desc else column.asc()
        self.order_by_clauses.append(order_clause)
        return self

    def order_by_desc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelSchema]":
        """ORDER BY column DESC"""
        return self.order_by(column, desc=True)

    def order_by_asc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelSchema]":
        """ORDER BY column ASC"""
        return self.order_by(column, desc=False)

    def clear_order(self) -> "QueryBuilder[ModelSchema]":
        """Очистить сортировку"""
        self.order_by_clauses = []
        return self

    async def find_all(self) -> list[ModelSchema]:
        """Выполнить запрос и вернуть все результаты"""
        return await self.repo.execute_typed_query(self)

    async def find_one(self) -> ModelSchema | None:
        """Выполнить запрос и вернуть первый результат"""
        original_limit = self.limit_value
        self.limit_value = 1

        try:
            results = await self.find_all()
            return results[0] if results else None
        finally:
            # Восстанавливаем исходный лимит
            self.limit_value = original_limit

    async def find_first(self) -> ModelSchema:
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