from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dplex import DPFilters, DPRepo, DPService
from dplex.internal.filters import DateTimeFilter, StringFilter, UUIDFilter
from dplex.internal.sort import NullsPlacement, Order, Sort


# ===================== 1) Модель =====================
class Base(DeclarativeBase): ...


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=datetime.now)


# ===================== 2) Pydantic-схемы =====================
class UserCreate(BaseModel):
    name: str
    email: str | None = None


class UserUpdate(BaseModel):
    # Используем маркер NULL, чтобы явно обнулить поле (NULL в БД)
    name: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    email: str | None
    created_at: datetime | None


# ===================== 3) Сортировка и фильтры =====================
class UserSortField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


class UserFilters(DPFilters[UserSortField]):
    """
    Набор фильтров для выборки пользователей.

    Позволяет выполнять фильтрацию по основным атрибутам модели `User`,
    включая точное совпадение, частичный поиск по строкам и фильтрацию по диапазону дат.

    Пример использования:
        filters = UserFilters(
            name=StringFilter(icontains="иван"),
            created_at=DateTimeFilter(gte=datetime(2024, 1, 1))
        )

    :param user_id: Фильтр по уникальному идентификатору пользователя (`UUIDFilter`).
                    Пример: `UUIDFilter(eq="550e8400-e29b-41d4-a716-446655440000")`
    :param name: Фильтр по имени пользователя (`StringFilter`).
                 Поддерживает операторы `eq`, `ne`, `like`, `ilike`, `contains`, `icontains`, `in`, `not_in`.
    :param email: Фильтр по адресу электронной почты (`StringFilter`).
                  Аналогично `name`, можно искать по шаблону или подстроке.
    :param created_at: Фильтр по дате создания (`DateTimeFilter`).
                       Поддерживает `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `between`.
    """

    user_id: UUIDFilter | None = None
    name: StringFilter | None = None
    email: StringFilter | None = None
    created_at: DateTimeFilter | None = None


# ===================== 4) Репозиторий =====================
class UserRepo(DPRepo[User, uuid.UUID]):
    """Минимальный репозиторий — всё берём у базового DPRepo"""

    def __init__(self, session: AsyncSession):
        # id_field_name должен соответствовать названию PK в модели
        super().__init__(model=User, session=session, id_field_name="user_id")


# ===================== 5) Сервис =====================
class UserService(
    DPService[
        User,  # SQLAlchemy модель
        uuid.UUID,  # Тип PK
        UserCreate,  # Схема создания
        UserUpdate,  # Схема обновления
        UserResponse,  # Схема ответа
        UserFilters,  # Схема фильтров (DPFilters-наследник)
        UserSortField,  # Enum полей сортировки
    ]
):
    """Базовый сервис без переопределений — всё автоматом"""

    def __init__(self, repo: UserRepo, session: AsyncSession):
        super().__init__(repository=repo, session=session, response_schema=UserResponse)


async def init_database(engine) -> None:
    """Создать все таблицы в БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ База данных инициализирована")


# ===================== 6) Пример использования =====================
# Пример асинхронного CRUD-потока с явной сортировкой
async def example_flow(session: AsyncSession) -> None:
    repo = UserRepo(session)
    service = UserService(repo, session)

    # ---- Create: создадим больше пользователей с разными email (в т.ч. @mail.ru)
    await service.create(UserCreate(name="Иван", email="ivan@example.com"))
    await service.create(UserCreate(name="Анна", email="anna@example.com"))
    await service.create(UserCreate(name="Борис", email="boris@mail.ru"))
    await service.create(UserCreate(name="Вера", email=None))
    await service.create(UserCreate(name="Григорий", email="grigoriy@mail.ru"))
    u = await service.create(
        UserCreate(name="Денис", email="denis@mail.com")
    )  # возьмём как 'u' для дальнейших операций
    print("✓ Users created")

    # ---- Read #1: ЯВНАЯ сортировка по ИМЕНИ (ASC), затем по ДАТЕ СОЗДАНИЯ (DESC, nulls last)
    users_by_name_then_created = await service.get_all(
        UserFilters(
            sort=[
                Sort(by=UserSortField.NAME, order=Order.ASC),  # 1-й ключ: name ASC
                Sort(
                    by=UserSortField.CREATED_AT,
                    order=Order.DESC,
                    nulls=NullsPlacement.LAST,
                ),  # 2-й ключ: created_at DESC NULLS LAST
            ],
            limit=50,
            offset=0,
        )
    )
    print("\nSorted by NAME ASC, then CREATED_AT DESC (NULLS LAST):")
    for it in users_by_name_then_created:
        print(f"  {it.name:10s} | {it.email or '-':20s} | {it.created_at}")

    # ---- Read #2: Фильтр только @mail.ru + ЯВНАЯ сортировка по ДАТЕ (DESC NULLS LAST), затем по ИМЕНИ (ASC)
    only_mail_ru = await service.get_all(
        UserFilters(
            email=StringFilter(ends_with="@mail.ru"),
            sort=[
                Sort(
                    by=UserSortField.CREATED_AT,
                    order=Order.DESC,
                    nulls=NullsPlacement.LAST,
                ),
                Sort(by=UserSortField.NAME, order=Order.ASC),
            ],
            limit=50,
            offset=0,
        )
    )
    print("\n@mail.ru ONLY — sorted by CREATED_AT DESC (NULLS LAST), then NAME ASC:")
    for it in only_mail_ru:
        print(f"  {it.name:10s} | {it.email or '-':20s} | {it.created_at}")

    # ---- Update: обнулим email у пользователя 'u' (NULL в БД)
    await service.update_by_id(u.user_id, UserUpdate(email=None))

    u2 = await service.get_by_id(u.user_id)

    print(f"\nUpdated (email -> NULL): {u2.user_id} | {u2.name} | {u2.email}")

    # ---- Exists / Count
    exists = await service.exists(UserFilters(user_id=UUIDFilter(eq=u.user_id)))
    total = await service.count(UserFilters())
    print("\nExists?", exists, "Total:", total)

    # ---- Delete
    deleted = await service.delete_by_id(u.user_id)
    print("Deleted?", deleted)

    # ---- Контрольная выборка после удаления: снова по имени
    after_delete = await service.get_all(
        UserFilters(
            sort=[Sort(by=UserSortField.NAME, order=Order.ASC)],
            limit=50,
            offset=0,
        )
    )
    print("\nAfter delete — sorted by NAME ASC:")
    for it in after_delete:
        print(f"  {it.name:10s} | {it.email or '-':20s} | {it.created_at}")


async def main() -> None:

    # Создание движка и сессии
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Инициализация БД
    await init_database(engine)

    # Создание фабрики сессий
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:

        await example_flow(session)


if __name__ == "__main__":
    asyncio.run(main())
