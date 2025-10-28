"""Query Builder для построения типизированных SQL запросов с поддержкой фильтрации и сортировки"""

from typing import TYPE_CHECKING, Any, Generic

from sqlalchemy import ColumnElement, asc, desc, nullsfirst, nullslast
from sqlalchemy.orm import InstrumentedAttribute

from dplex.internal.types import ModelType

if TYPE_CHECKING:
    from dplex.dp_repo import DPRepo

from dplex.internal.sort import NullsPlacement, Sort, Order


class QueryBuilder(Generic[ModelType]):
    """
    Query Builder для построения типизированных SQL запросов

    Предоставляет fluent interface для построения SQL запросов с поддержкой:
    - Фильтрации (WHERE условия)
    - Сортировки (ORDER BY с управлением NULL)
    - Пагинации (LIMIT/OFFSET)
    - Выполнения запросов (find_all, find_one, count, exists)

    Type Parameters:
        ModelType: Тип SQLAlchemy модели

    Attributes:
        repo: Репозиторий для выполнения запросов
        model: Класс SQLAlchemy модели
        filters: Список условий фильтрации
        limit_value: Значение LIMIT
        offset_value: Значение OFFSET
        order_by_clauses: Список условий сортировки
    """

    def __init__(self, repo: "DPRepo[ModelType, Any]", model: type[ModelType]) -> None:
        """
        Инициализация Query Builder

        Args:
            repo: Репозиторий для выполнения запросов
            model: Класс SQLAlchemy модели

        Returns:
            None
        """
        self.repo = repo
        self.model = model
        self.filters: list[ColumnElement[bool]] = []
        self.limit_value: int | None = None
        self.offset_value: int | None = None
        self.order_by_clauses: list[Any] = []

    def where(self, condition: ColumnElement[bool]) -> "QueryBuilder[ModelType]":
        """
        Добавить WHERE условие

        Принимает готовое SQLAlchemy условие фильтрации.

        Args:
            condition: SQLAlchemy условие фильтрации (ColumnElement[bool])

        Returns:
            Self для цепочки вызовов
        """
        self.filters.append(condition)
        return self

    def where_eq(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column = value

        Args:
            column: Колонка модели
            value: Значение для сравнения

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column == value
        return self.where(condition)

    def where_ne(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column != value

        Args:
            column: Колонка модели
            value: Значение для исключения

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column != value
        return self.where(condition)

    def where_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column IN (values)

        Args:
            column: Колонка модели
            values: Список допустимых значений

        Returns:
            Self для цепочки вызовов

        Note:
            Если список пустой, добавляется условие которое всегда false
        """
        if not values:
            # Если список пустой, добавляем условие которое всегда false
            condition: ColumnElement[bool] = column.in_([])
        else:
            condition = column.in_(values)
        return self.where(condition)

    def where_not_in(
        self, column: InstrumentedAttribute[Any], values: list[Any]
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column NOT IN (values)

        Args:
            column: Колонка модели
            values: Список исключаемых значений

        Returns:
            Self для цепочки вызовов

        Note:
            Если список пустой, условие не добавляется (всегда true)
        """
        if not values:
            # Если список пустой, условие всегда true - не добавляем фильтр
            return self
        condition: ColumnElement[bool] = ~column.in_(values)
        return self.where(condition)

    def where_is_null(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column IS NULL

        Args:
            column: Колонка модели

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column.is_(None)
        return self.where(condition)

    def where_is_not_null(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column IS NOT NULL

        Args:
            column: Колонка модели

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column.isnot(None)
        return self.where(condition)

    def where_like(
        self, column: InstrumentedAttribute[Any], pattern: str
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column LIKE pattern (с учетом регистра)

        Args:
            column: Колонка модели
            pattern: Шаблон поиска (используйте % и _ как wildcards)

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column.like(pattern)
        return self.where(condition)

    def where_ilike(
        self, column: InstrumentedAttribute[Any], pattern: str
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column ILIKE pattern (без учета регистра)

        Args:
            column: Колонка модели
            pattern: Шаблон поиска (используйте % и _ как wildcards)

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column.ilike(pattern)
        return self.where(condition)

    def where_between(
        self, column: InstrumentedAttribute[Any], start: Any, end: Any
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column BETWEEN start AND end

        Args:
            column: Колонка модели
            start: Начальное значение диапазона (включительно)
            end: Конечное значение диапазона (включительно)

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column.between(start, end)
        return self.where(condition)

    def where_gt(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column > value (больше чем)

        Args:
            column: Колонка модели
            value: Значение для сравнения

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column > value
        return self.where(condition)

    def where_gte(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column >= value (больше или равно)

        Args:
            column: Колонка модели
            value: Значение для сравнения

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column >= value
        return self.where(condition)

    def where_lt(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column < value (меньше чем)

        Args:
            column: Колонка модели
            value: Значение для сравнения

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column < value
        return self.where(condition)

    def where_lte(
        self, column: InstrumentedAttribute[Any], value: Any
    ) -> "QueryBuilder[ModelType]":
        """
        WHERE column <= value (меньше или равно)

        Args:
            column: Колонка модели
            value: Значение для сравнения

        Returns:
            Self для цепочки вызовов
        """
        condition: ColumnElement[bool] = column <= value
        return self.where(condition)

    def limit(self, limit: int) -> "QueryBuilder[ModelType]":
        """
        LIMIT - ограничить количество записей

        Args:
            limit: Максимальное количество записей (должно быть >= 0)

        Returns:
            Self для цепочки вызовов

        Raises:
            ValueError: Если limit отрицательный
        """
        if limit < 0:
            raise ValueError("Limit must be non-negative")
        self.limit_value = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder[ModelType]":
        """
        OFFSET - пропустить количество записей

        Args:
            offset: Количество пропускаемых записей (должно быть >= 0)

        Returns:
            Self для цепочки вызовов

        Raises:
            ValueError: Если offset отрицательный
        """
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        self.offset_value = offset
        return self

    def paginate(self, page: int, per_page: int) -> "QueryBuilder[ModelType]":
        """
        Пагинация - устанавливает LIMIT и OFFSET на основе номера страницы

        Args:
            page: Номер страницы (начинается с 1)
            per_page: Количество записей на странице

        Returns:
            Self для цепочки вызовов

        Raises:
            ValueError: Если page < 1 или per_page < 1
        """
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
        ORDER BY column - добавить сортировку

        Args:
            column: Колонка для сортировки
            desc_order: True для DESC (по убыванию), False для ASC (по возрастанию)

        Returns:
            Self для цепочки вызовов
        """
        order_clause = column.desc() if desc_order else column.asc()
        self.order_by_clauses.append(order_clause)
        return self

    def order_by_desc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """
        ORDER BY column DESC - сортировка по убыванию

        Args:
            column: Колонка для сортировки

        Returns:
            Self для цепочки вызовов
        """
        return self.order_by(column, desc_order=True)

    def order_by_asc(
        self, column: InstrumentedAttribute[Any]
    ) -> "QueryBuilder[ModelType]":
        """
        ORDER BY column ASC - сортировка по возрастанию

        Args:
            column: Колонка для сортировки

        Returns:
            Self для цепочки вызовов
        """
        return self.order_by(column, desc_order=False)

    def order_by_with_nulls(
        self,
        column: InstrumentedAttribute[Any],
        desc_order: bool = False,
        nulls_placement: NullsPlacement | None = None,
    ) -> "QueryBuilder[ModelType]":
        """
        ORDER BY column с управлением размещением NULL значений

        Args:
            column: Колонка для сортировки
            desc_order: True для DESC, False для ASC
            nulls_placement: Размещение NULL (FIRST или LAST)

        Returns:
            Self для цепочки вызовов
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

        Returns:
            Self для цепочки вызовов
        """
        desc_order = sort_item.order == Order.DESC
        return self.order_by_with_nulls(column, desc_order, sort_item.nulls)

    def apply_sorts(
        self,
        sort_list: list[Sort[Any]],
        column_mapper: dict[Any, InstrumentedAttribute[Any]],
    ) -> "QueryBuilder[ModelType]":
        """
        Применить список Sort объектов к query builder

        Позволяет применить множественную сортировку из списка Sort объектов.
        Использует маппер для преобразования полей enum в колонки модели.

        Args:
            sort_list: Список объектов Sort
            column_mapper: Словарь для маппинга field -> column

        Returns:
            Self для цепочки вызовов

        Raises:
            ValueError: Если для поля не найден маппинг колонки
        """
        for sort_item in sort_list:
            column = column_mapper.get(sort_item.by)
            if column is None:
                raise ValueError(f"Column mapping not found for field: {sort_item.by}")
            self.apply_sort(sort_item, column)
        return self

    def clear_order(self) -> "QueryBuilder[ModelType]":
        """
        Очистить все условия сортировки

        Returns:
            Self для цепочки вызовов
        """
        self.order_by_clauses = []
        return self

    async def find_all(self) -> list[ModelType]:
        """
        Выполнить запрос и вернуть все результаты

        Returns:
            Список моделей, соответствующих запросу
        """
        return await self.repo.execute_typed_query(self)

    async def find_one(self) -> ModelType | None:
        """
        Выполнить запрос и вернуть первый результат или None

        Автоматически устанавливает LIMIT 1.

        Returns:
            Первая модель из результатов или None если ничего не найдено
        """
        self.limit_value = 1
        results = await self.find_all()
        return results[0] if results else None

    async def find_first(self) -> ModelType:
        """
        Выполнить запрос и вернуть первый результат или вызвать ошибку

        Аналогично find_one(), но вызывает ValueError если ничего не найдено.

        Returns:
            Первая модель из результатов

        Raises:
            ValueError: Если запрос не вернул результатов
        """
        result = await self.find_one()
        if result is None:
            raise ValueError(f"No {self.model.__name__} found matching criteria")
        return result

    async def count(self) -> int:
        """
        Подсчитать количество записей соответствующих запросу

        Выполняет COUNT запрос без выборки данных.

        Returns:
            Количество записей
        """
        return await self.repo.execute_typed_count(self)

    async def exists(self) -> bool:
        """
        Проверить существование записей соответствующих запросу

        Эквивалентно count() > 0, но более выразительно.

        Returns:
            True если хотя бы одна запись найдена, иначе False
        """
        count = await self.count()
        return count > 0
