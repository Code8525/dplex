import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select, func, and_, delete, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute

from dataplex import QueryBuilder
from dataplex.types import KeyType

ModelSchema = TypeVar("ModelSchema", bound=DeclarativeBase)



class BaseDBRepo(Generic[ModelSchema, KeyType]):
    """Базовый репозиторий с улучшенной типизацией"""

    def __init__(
        self,
        model: type[ModelSchema],
        session: AsyncSession,
        key_type: type[KeyType] = uuid.UUID,
        id_field_name: str = "id",
    ) -> None:
        self.model = model
        self.session = session
        self.key_type = key_type
        self.id_field_name = id_field_name
        # ✅ Кешируем ID колонку при инициализации
        self._id_column = self._get_id_column()

    def _get_id_column(self) -> InstrumentedAttribute[KeyType]:
        """Получить типизированную ID колонку"""
        column = getattr(self.model, self.id_field_name)
        if not isinstance(column, InstrumentedAttribute):
            raise ValueError(
                f"Field '{self.id_field_name}' is not a valid SQLAlchemy column"
            )
        return column

    def query(self) -> "QueryBuilder[ModelSchema]":
        """Создать типизированный query builder"""
        return QueryBuilder(self, self.model)

    def id_eq(self, value: KeyType) -> ColumnElement[bool]:
        """Возвращает условие для сравнения ID с entity_id"""
        return self._id_column == value

    def id_in(self, values: list[KeyType]) -> ColumnElement[bool]:
        """Возвращает условие для проверки ID в списке значений"""
        return self._id_column.in_(values)

    # Методы с использованием закешированной колонки
    async def find_by_id(self, entity_id: KeyType) -> ModelSchema | None:
        """Найти сущность по ID"""
        return await self.query().where(self.id_eq(entity_id)).find_one()

    async def find_by_ids(self, entity_ids: list[KeyType]) -> list[ModelSchema]:
        """Найти сущности по списку ID"""
        return await self.query().where(self.id_in(entity_ids)).find_all()

    async def delete_by_id(self, entity_id: KeyType) -> None:
        """Удалить сущность по ID"""
        stmt = delete(self.model).where(self.id_eq(entity_id))
        await self.session.execute(stmt)

    async def delete_by_ids(self, entity_ids: list[KeyType]) -> None:
        """Удалить сущности по ID"""
        stmt = delete(self.model).where(self.id_in(entity_ids))
        await self.session.execute(stmt)

    async def update_by_id(self, entity_id: KeyType, values: dict[str, Any]) -> None:
        """Обновить сущность по ID"""
        stmt = update(self.model).where(self.id_eq(entity_id)).values(**values)
        await self.session.execute(stmt)

    async def update_by_ids(
        self, entity_ids: list[KeyType], values: dict[str, Any]
    ) -> None:
        """Обновить сущности по ID"""
        stmt = update(self.model).where(self.id_in(entity_ids)).values(**values)
        await self.session.execute(stmt)

    async def exists_by_id(self, entity_id: KeyType) -> bool:
        """Проверить существование сущности по ID"""
        count = await self.query().where(self.id_eq(entity_id)).count()
        return count > 0

    async def create(self, entity: ModelSchema) -> ModelSchema:
        """Создать новую сущность"""
        self.session.add(entity)
        return entity

    async def create_bulk(self, entities: list[ModelSchema]) -> list[ModelSchema]:
        """Создать несколько сущностей"""
        self.session.add_all(entities)
        return entities

    async def save_changes(self) -> None:
        """Сохранить изменения в базе данных"""
        await self.session.commit()

    async def rollback(self) -> None:
        """Откатить изменения"""
        await self.session.rollback()

    # Методы для выполнения запросов билдера
    async def execute_typed_query(
        self, builder: "QueryBuilder[ModelSchema]"
    ) -> list[ModelSchema]:
        """Выполнить типизированный запрос"""
        stmt = select(self.model)

        if builder.filters:
            stmt = stmt.where(and_(*builder.filters))

        if builder.order_by_clauses:
            stmt = stmt.order_by(*builder.order_by_clauses)

        if builder.limit_value is not None:
            stmt = stmt.limit(builder.limit_value)

        if builder.offset_value is not None:
            stmt = stmt.offset(builder.offset_value)

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def execute_typed_count(self, builder: "QueryBuilder[ModelSchema]") -> int:
        """Подсчитать записи через типизированный билдер"""
        stmt = select(func.count()).select_from(self.model)

        if builder.filters:
            stmt = stmt.where(and_(*builder.filters))

        result = await self.session.execute(stmt)
        return result.scalar_one()


