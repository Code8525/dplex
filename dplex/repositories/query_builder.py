from typing import Any, Generic
from sqlalchemy import ColumnElement
from sqlalchemy.orm import InstrumentedAttribute

from dplex.repositories.repository import DPRepo
from dplex.types import ModelType


class QueryBuilder(Generic[ModelType]):
    """Query Builder с улучшенной типизацией"""

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
        self, column: InstrumentedAttribute[Any], desc: bool = False
    ) -> "QueryBuilder[ModelType]":
        """ORDER BY column"""
        order_clause = column.desc() if desc else column.asc()
        self.order_by_clauses.append(order_clause)
        return self

    def order_by_desc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """ORDER BY column DESC"""
        return self.order_by(column, desc=True)

    def order_by_asc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """ORDER BY column ASC"""
        return self.order_by(column, desc=False)

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
