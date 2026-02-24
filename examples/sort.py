"""
Примеры сортировки в dplex.

Показывает:
- Обычную сортировку по полю (Sort(by=..., order=...))
- Опциональный sort_by: Sort(by=request.sort_by, order=...) — при sort_by=None сортировка не применяется
- Опциональный sort_by с отдельным enum в API: filters.add_sort_from_value(api_sort_by, order)
- Множественную сортировку и NullsPlacement
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dplex import DPFilters, DPRepo, DPService
from dplex.internal.filters import StringFilter
from dplex.internal.sort import NullsPlacement, Order, Sort


# ===================== Модель и схемы =====================
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=datetime.now)


class UserCreate(BaseModel):
    name: str
    email: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    created_at: datetime


# ===================== Сортировка и фильтры =====================
class UserSortField(StrEnum):
    """Поля для сортировки."""

    ID = "id"
    NAME = "name"
    EMAIL = "email"
    CREATED_AT = "created_at"


class UserFilters(DPFilters[UserSortField]):
    """Фильтры пользователей (в примерах используем в основном sort/limit/offset)."""

    name: StringFilter | None = None


class UserRepo(DPRepo[User, int]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=User, session=session, id_field_name="id")


class UserService(
    DPService[
        User,
        int,
        UserCreate,
        UserUpdate,
        UserResponse,
        UserFilters,
        UserSortField,
    ]
):
    def __init__(self, repo: UserRepo, session: AsyncSession):
        super().__init__(repository=repo, session=session, response_schema=UserResponse)


# ===================== Эмуляция API-запроса (опциональный sort_by) =====================
class QueryRequest(BaseModel):
    """Базовый запрос списка с опциональной сортировкой (как в типовом API)."""

    sort: Order = Field(default=Order.DESC, description="Направление сортировки")
    sort_by: UserSortField | None = Field(
        default=None,
        description="Поле сортировки; если не указано — сортировка не применяется",
    )
    limit: int | None = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def request_to_filters(request: QueryRequest) -> UserFilters:
    """
    Преобразование API-запроса в фильтры dplex.

    Можно писать просто Sort(by=request.sort_by, order=request.sort).
    При request.sort_by is None сортировка не применяется.
    """
    return UserFilters(
        sort=[
            Sort(
                by=request.sort_by,
                order=request.sort,
            ),
        ],
        limit=request.limit,
        offset=request.offset,
    )


# ===================== Эмуляция API-запроса (api enum как подмножество доменного) =====================
class ApiUserSortBy(StrEnum):
    """
    Поля сортировки на уровне API.

    Часто в API хочется разрешить сортировку только по части полей доменной модели.
    В dplex сортировка далее использует `sort_field.value`, поэтому можно передавать StrEnum напрямую.
    """

    NAME = "name"
    CREATED_AT = "created_at"


class QueryRequestApiSortBy(BaseModel):
    """Запрос списка, где sort_by типизирован отдельным API enum."""

    sort: Order = Field(default=Order.DESC, description="Направление сортировки")
    sort_by: ApiUserSortBy | None = Field(
        default=None,
        description="Поле сортировки; если не указано — сортировка не применяется",
    )
    limit: int | None = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def request_to_filters_from_value(request: QueryRequestApiSortBy) -> UserFilters:
    """
    Преобразование API-запроса в фильтры dplex, когда sort_by — отдельный enum.

    Создаём фильтры и добавляем сортировку методом экземпляра:
    `filters.add_sort_from_value(request.sort_by, request.sort)`.
    """
    filters = UserFilters(limit=request.limit, offset=request.offset)
    filters.add_sort_from_value(request.sort_by, request.sort)
    return filters


# ===================== Примеры =====================
async def example_basic_sort(service: UserService) -> None:
    """Обычная сортировка по одному полю."""
    print("\n--- Сортировка по имени ASC ---")
    filters = UserFilters(
        sort=Sort(by=UserSortField.NAME, order=Order.ASC),
        limit=5,
    )
    users = await service.get_all(filters)
    for u in users:
        print(f"  {u.name} | {u.email or '-'}")


async def example_sort_desc_with_nulls(service: UserService) -> None:
    """Сортировка по убыванию с явным размещением NULL (по email: NULL в конце)."""
    print("\n--- Сортировка по email DESC, NULLS LAST ---")
    filters = UserFilters(
        sort=Sort(
            by=UserSortField.EMAIL,
            order=Order.DESC,
            nulls=NullsPlacement.LAST,
        ),
        limit=10,
    )
    users = await service.get_all(filters)
    for u in users:
        print(f"  {u.name} | {u.email or '(NULL)'}")


async def example_sort_asc_with_nulls(service: UserService) -> None:
    """Сортировка по возрастанию с явным размещением NULL (по email: NULL в начале)."""
    print("\n--- Сортировка по email ASC, NULLS FIRST ---")
    filters = UserFilters(
        sort=Sort(
            by=UserSortField.EMAIL,
            order=Order.ASC,
            nulls=NullsPlacement.FIRST,
        ),
        limit=10,
    )
    users = await service.get_all(filters)
    for u in users:
        print(f"  {u.name} | {u.email or '(NULL)'}")


async def example_multiple_sort(service: UserService) -> None:
    """Множественная сортировка: сначала по имени, затем по дате."""
    print("\n--- Множественная сортировка: NAME ASC, затем CREATED_AT DESC ---")
    filters = UserFilters(
        sort=[
            Sort(by=UserSortField.NAME, order=Order.ASC),
            Sort(by=UserSortField.CREATED_AT, order=Order.DESC),
        ],
        limit=10,
    )
    users = await service.get_all(filters)
    for u in users:
        print(f"  {u.name} | {u.created_at}")


async def example_optional_sort_by_no_field(service: UserService) -> None:
    """
    Типовой запрос без указания sort_by.
    Sort(by=None, order=...) — dplex не применяет сортировку.
    """
    print("\n--- Запрос без sort_by (сортировка не применяется) ---")
    request = QueryRequest(sort_by=None, sort=Order.DESC, limit=5)
    filters = request_to_filters(request)
    print(f"  has_sort() = {filters.has_sort()}")
    users = await service.get_all(filters)
    print(f"  Получено записей: {len(users)} (порядок — как в БД, без ORDER BY)")


async def example_optional_sort_by_with_field(service: UserService) -> None:
    """Запрос с указанным sort_by — сортировка применяется."""
    print("\n--- Запрос с sort_by=NAME, sort=ASC ---")
    request = QueryRequest(
        sort_by=UserSortField.NAME,
        sort=Order.ASC,
        limit=5,
    )
    filters = request_to_filters(request)
    print(f"  has_sort() = {filters.has_sort()}")
    users = await service.get_all(filters)
    for u in users:
        print(f"  {u.name} | {u.email or '-'}")


async def example_single_sort_with_by_none(service: UserService) -> None:
    """Явная передача одного Sort(by=None) — эквивалентно отсутствию сортировки."""
    print("\n--- Один элемент Sort(by=None) ---")
    filters = UserFilters(
        sort=Sort(by=None, order=Order.DESC),
        limit=5,
    )
    print(f"  has_sort() = {filters.has_sort()}")
    users = await service.get_all(filters)
    print(f"  Записей: {len(users)} (без сортировки)")


async def example_from_value_api_enum_subset(service: UserService) -> None:
    """
    Пример `filters.add_sort_from_value()`:

    - В API используется отдельный enum (подмножество доменного).
    - sort_by опционален, при None сортировка не применяется.
    """
    print("\n--- add_sort_from_value(): API enum как подмножество доменного ---")
    request = QueryRequestApiSortBy(
        sort_by=ApiUserSortBy.CREATED_AT,
        sort=Order.DESC,
        limit=5,
    )
    filters = request_to_filters_from_value(request)
    print(f"  has_sort() = {filters.has_sort()}")
    # Для вывода: sort может быть одним Sort или списком
    if filters.sort is not None:
        first = filters.sort[0] if isinstance(filters.sort, list) else filters.sort
        by_value = first.by.value if first.by is not None else None
        print(f"  sort.by = {first.by} (value={by_value})")

    users = await service.get_all(filters)
    for u in users:
        print(f"  {u.name} | {u.created_at}")


async def init_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def run_all(service: UserService) -> None:
    await example_basic_sort(service)
    await example_sort_desc_with_nulls(service)
    await example_sort_asc_with_nulls(service)
    await example_multiple_sort(service)
    await example_optional_sort_by_no_field(service)
    await example_optional_sort_by_with_field(service)
    await example_single_sort_with_by_none(service)
    await example_from_value_api_enum_subset(service)


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    await init_db(engine)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        repo = UserRepo(session)
        service = UserService(repo, session)
        # Создаём тестовые данные
        for name, email in [
            ("Алиса", "alice@example.com"),
            ("Боб", None),
            ("Вера", "vera@example.com"),
            ("Глеб", "gleb@example.com"),
            ("Дарья", None),
        ]:
            await service.create(UserCreate(name=name, email=email))

        print("=" * 60)
        print("ПРИМЕРЫ СОРТИРОВКИ (dplex)")
        print("=" * 60)
        await run_all(service)
        print("\n" + "=" * 60)
        print("Готово.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
