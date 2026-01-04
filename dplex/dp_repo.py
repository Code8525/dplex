"""Базовый репозиторий для работы с SQLAlchemy моделями"""

from typing import Any

from sqlalchemy import ColumnElement, and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from dplex.internal.query_builder import QueryBuilder


class DPRepo[ModelType, KeyType]:
    """
    Базовый репозиторий для работы с SQLAlchemy моделями
    Предоставляет стандартные CRUD операции и интеграцию с QueryBuilder
    для построения сложных запросов. Поддерживает различные типы первичных ключей.

    Type Parameters:
        ModelType: Тип SQLAlchemy модели
        KeyType: Тип первичного ключа (int, str, uuid.UUID)

    Attributes:
        model: Класс SQLAlchemy модели
        session: Асинхронная сессия SQLAlchemy
        id_field_name: Имя поля первичного ключа в модели
    """

    def __init__(
        self,
        model: type[ModelType],
        session: AsyncSession,
        id_field_name: str = "id",
    ) -> None:
        """
        Инициализация репозитория

        Args:
            model: Класс SQLAlchemy модели
            session: Асинхронная сессия SQLAlchemy
            id_field_name: Имя поля первичного ключа (по умолчанию "id")

        Returns:
            None

        Raises:
            ValueError: Если поле id_field_name отсутствует в модели или не является SQLAlchemy колонкой
        """
        self.model = model
        self.session = session
        self.id_field_name = id_field_name
        self._id_column = self._get_id_column()

    def _get_id_column(self) -> InstrumentedAttribute[KeyType]:
        """
        Получить типизированную ID колонку модели

        Returns:
            SQLAlchemy колонка первичного ключа

        Raises:
            ValueError: Если поле не найдено или не является SQLAlchemy колонкой
        """
        if not hasattr(self.model, self.id_field_name):
            raise ValueError(
                f"Model {self.model.__name__} does not have field '{self.id_field_name}'"
            )

        column = getattr(self.model, self.id_field_name)

        # Проверяем что это SQLAlchemy column
        if not hasattr(column, "property"):
            raise ValueError(
                f"Field '{self.id_field_name}' in {self.model.__name__} is not a SQLAlchemy column"
            )

        return column

    def query(self) -> "QueryBuilder[ModelType]":
        """
        Создать типизированный query builder

        Returns:
            Новый экземпляр QueryBuilder для построения запросов
        """
        return QueryBuilder(self, self.model)

    def id_eq(self, value: KeyType) -> ColumnElement[bool]:
        """
        Создать условие для сравнения ID с заданным значением

        Args:
            value: Значение ID для сравнения

        Returns:
            SQLAlchemy условие (id == value)
        """
        return self._id_column == value

    def id_in(self, values: list[KeyType]) -> ColumnElement[bool]:
        """
        Создать условие для проверки ID в списке значений

        Args:
            values: Список значений ID

        Returns:
            SQLAlchemy условие (id IN values)
        """
        return self._id_column.in_(values)

    async def find_by_id(self, entity_id: KeyType) -> ModelType | None:
        """
        Найти сущность по ID

        Args:
            entity_id: ID сущности

        Returns:
            Модель или None если не найдена
        """
        return await self.query().where(self.id_eq(entity_id)).find_one()

    async def find_by_ids(self, entity_ids: list[KeyType]) -> list[ModelType]:
        """
        Найти сущности по списку ID

        Args:
            entity_ids: Список ID сущностей

        Returns:
            Список найденных моделей

        Raises:
            ValueError: Если список ID пустой
        """
        if not entity_ids:
            raise ValueError("DPRepo.find_by_ids: Список ID не может быть пустым")

        return await self.query().where(self.id_in(entity_ids)).find_all()

    async def delete_by_query_builder(
        self,
        query_builder: "QueryBuilder[ModelType]",
    ) -> None:
        """
        Массовое удаление по условиям из QueryBuilder
        Использует централизованную логику построения WHERE.

        Args:
            query_builder: QueryBuilder с условиями фильтрации

        Returns:
            None

        Raises:
            ValueError: Если не указано ни одного условия WHERE
        """
        condition = self._build_where_clause_from_builder(query_builder)
        if condition is None:
            raise ValueError(
                "DPRepo.delete_by_query_builder: требуется хотя бы одно условие WHERE для массового удаления"
            )

        stmt = delete(self.model).where(condition)
        await self.session.execute(stmt)

    async def delete_by_id(self, entity_id: KeyType) -> None:
        """
        Удалить сущность по ID

        Args:
            entity_id: ID сущности для удаления

        Returns:
            None
        """
        stmt = delete(self.model).where(self.id_eq(entity_id))
        await self.session.execute(stmt)

    async def delete_by_ids(self, entity_ids: list[KeyType]) -> None:
        """
        Удалить сущности по списку ID

        Args:
            entity_ids: Список ID сущностей для удаления

        Returns:
            None

        Raises:
            ValueError: Если список ID пустой
        """
        if not entity_ids:
            raise ValueError("DPRepo.delete_by_ids: Список ID не может быть пустым")

        stmt = delete(self.model).where(self.id_in(entity_ids))
        await self.session.execute(stmt)

    async def update(
        self,
        where: ColumnElement[bool] | list[ColumnElement[bool]] | None,
        values: dict[str, Any],
    ) -> None:
        """
        Универсальный UPDATE по условию(ям)

        Args:
            where: Условие WHERE (одно или список условий)
            values: Словарь с обновляемыми полями и значениями

        Returns:
            None

        Raises:
            ValueError: Если where равен None, пустой список или values пустой
        """
        if not values:
            raise ValueError(
                "DPRepo.update: Данные для обновления не могут быть пустыми"
            )

        if where is None:
            raise ValueError("DPRepo.update: пустой WHERE запрещён")

        condition: ColumnElement[bool]
        if isinstance(where, list):
            if not where:
                raise ValueError("DPRepo.update: пустой список условий WHERE запрещён")
            condition = and_(*where)
        else:
            condition = where

        stmt = update(self.model).where(condition).values(**values)
        await self.session.execute(stmt)

    async def update_by_query_builder(
        self,
        query_builder: "QueryBuilder[ModelType]",
        values: dict[str, Any],
    ) -> None:
        """
        Массовое обновление по условиям из QueryBuilder

        Args:
            query_builder: QueryBuilder с условиями фильтрации
            values: Словарь с обновляемыми полями и значениями

        Returns:
            None

        Raises:
            ValueError: Если не указано ни одного условия WHERE или values пустой
        """
        if not values:
            raise ValueError(
                "DPRepo.update_by_query_builder: Данные для обновления не могут быть пустыми"
            )

        condition = self._build_where_clause_from_builder(query_builder)
        if condition is None:
            raise ValueError(
                "DPRepo.update_by_query_builder: требуется хотя бы одно условие WHERE"
            )

        stmt = update(self.model).where(condition).values(**values)
        await self.session.execute(stmt)

    async def update_by_id(self, entity_id: KeyType, values: dict[str, Any]) -> None:
        """
        Обновить сущность по ID

        Args:
            entity_id: ID сущности
            values: Словарь с обновляемыми полями и значениями

        Returns:
            None

        Raises:
            ValueError: Если values пустой
        """
        if not values:
            raise ValueError(
                "DPRepo.update_by_id: Данные для обновления не могут быть пустыми"
            )

        stmt = update(self.model).where(self.id_eq(entity_id)).values(**values)
        await self.session.execute(stmt)

    async def update_by_ids(
        self, entity_ids: list[KeyType], values: dict[str, Any]
    ) -> None:
        """
        Обновить сущности по списку ID

        Args:
            entity_ids: Список ID сущностей
            values: Словарь с обновляемыми полями и значениями

        Returns:
            None

        Raises:
            ValueError: Если entity_ids или values пустые
        """
        if not entity_ids:
            raise ValueError("DPRepo.update_by_ids: Список ID не может быть пустым")

        if not values:
            raise ValueError(
                "DPRepo.update_by_ids: Данные для обновления не могут быть пустыми"
            )

        stmt = update(self.model).where(self.id_in(entity_ids)).values(**values)
        await self.session.execute(stmt)

    async def exists_by_id(self, entity_id: KeyType) -> bool:
        """
        Проверить существование сущности по ID

        Args:
            entity_id: ID сущности

        Returns:
            True если сущность существует, иначе False
        """
        count = await self.query().where(self.id_eq(entity_id)).count()
        return count > 0

    async def create(self, entity: ModelType) -> ModelType:
        """
        Создать новую сущность
        Добавляет сущность в сессию. Требует вызов commit() для сохранения.

        Args:
            entity: Экземпляр модели для создания

        Returns:
            Созданный экземпляр модели
        """
        self.session.add(entity)
        return entity

    async def create_bulk(self, entities: list[ModelType]) -> list[ModelType]:
        """
        Создать несколько сущностей
        Добавляет сущности в сессию. Требует вызов commit() для сохранения.

        Args:
            entities: Список экземпляров модели для создания

        Returns:
            Список созданных экземпляров модели

        Raises:
            ValueError: Если список entities пустой
        """
        if not entities:
            raise ValueError(
                "DPRepo.create_bulk: Список для создания не может быть пустым"
            )

        self.session.add_all(entities)
        return entities

    async def commit(self) -> None:
        """
        Сохранить изменения в базе данных
        Фиксирует все изменения в текущей транзакции.

        Returns:
            None
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """
        Откатить изменения
        Отменяет все изменения в текущей транзакции.

        Returns:
            None
        """
        await self.session.rollback()

    @staticmethod
    def _build_where_clause_from_builder(
        builder: "QueryBuilder[ModelType]",
    ) -> ColumnElement[bool] | None:
        """
        Построить единое WHERE условие из фильтров QueryBuilder

        Args:
            builder: QueryBuilder с условиями фильтрации

        Returns:
            Объединенное условие WHERE или None если фильтров нет
        """
        if builder.filters:
            return and_(*builder.filters)
        return None

    async def execute_typed_query(
        self, builder: "QueryBuilder[ModelType]"
    ) -> list[ModelType]:
        """
        Выполнить типизированный запрос из QueryBuilder
        Применяет все условия фильтрации, сортировки и пагинации из builder.

        Args:
            builder: QueryBuilder с параметрами запроса

        Returns:
            Список найденных моделей
        """
        stmt = select(self.model)

        condition = self._build_where_clause_from_builder(builder)
        if condition is not None:
            stmt = stmt.where(condition)

        if builder.order_by_clauses:
            stmt = stmt.order_by(*builder.order_by_clauses)

        if builder.limit_value is not None:
            stmt = stmt.limit(builder.limit_value)

        if builder.offset_value is not None:
            stmt = stmt.offset(builder.offset_value)

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def execute_typed_count(self, builder: "QueryBuilder[ModelType]") -> int:
        """
        Подсчитать записи через типизированный QueryBuilder
        Применяет только условия фильтрации из builder.

        Args:
            builder: QueryBuilder с условиями фильтрации

        Returns:
            Количество записей
        """
        stmt = select(func.count()).select_from(self.model)

        condition = self._build_where_clause_from_builder(builder)
        if condition is not None:
            stmt = stmt.where(condition)

        result = await self.session.execute(stmt)
        return result.scalar_one()
