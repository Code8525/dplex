"""
Примеры сортировки в dplex.

Разделение схем:
- Доменная схема: UserSortField, UserFilters — используются внутри приложения (сервис, DPFilters).
- API-схема: QueryRequest / QueryRequestApiSortBy — то, что приходит с клиента (query-параметры).

Показывает:
- Обычную сортировку по полю (Sort(by=..., order=...))
- Опциональный sort_by: при sort_by=None сортировка не применяется
- API-схема с подмножеством полей: свой enum (ApiUserSortBy) → filters.add_sort(api_sort_by, order) в доменные фильтры
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


# ===================== Доменная схема (сортировка и фильтры) =====================
# Используется внутри приложения: сервис, репозиторий, DPFilters.
# Enum задаёт все поля модели, по которым разрешена сортировка в домене.


class UserSortField(StrEnum):
    """Доменные поля сортировки — все поля User, по которым можно сортировать."""

    ID = "id"
    NAME = "name"
    EMAIL = "email"
    CREATED_AT = "created_at"


class UserFilters(DPFilters[UserSortField]):
    """Доменная схема фильтров: тип сортировки зафиксирован как UserSortField."""

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


# ===================== API-схема: запрос с тем же enum, что и домен =====================
# Когда в API принимается тот же enum, что и в домене (UserSortField), маппинг не нужен.


class QueryRequest(BaseModel):
    """Схема запроса API: sort_by совпадает с доменным UserSortField."""

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


# ===================== API-схема: свой enum (подмножество доменного) =====================
# В API часто разрешают сортировать только по части полей. Отдельный enum для запроса,
# значения (.value) совпадают с доменным — тогда add_sort(api_sort_by, ...) передаёт в доменные фильтры.


class ApiUserSortBy(StrEnum):
    """
    API-схема полей сортировки — подмножество доменного UserSortField.

    В запросе клиента разрешены только NAME и CREATED_AT. Значения совпадают с доменом,
    поэтому в add_sort() можно передать этот enum напрямую.
    """

    NAME = "name"
    CREATED_AT = "created_at"


class QueryRequestApiSortBy(BaseModel):
    """Схема запроса API: sort_by типизирован API-enum (не доменным)."""

    sort: Order = Field(default=Order.DESC, description="Направление сортировки")
    sort_by: ApiUserSortBy | None = Field(
        default=None,
        description="Поле сортировки; если не указано — сортировка не применяется",
    )
    limit: int | None = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def request_to_filters_from_value(request: QueryRequestApiSortBy) -> UserFilters:
    """
    API-схема → доменные фильтры: sort_by приходит как ApiUserSortBy, фильтры ждут UserSortField.

    add_sort() принимает любой StrEnum с подходящим .value; тип Sort[UserSortField] задаётся
    доменной схемой UserFilters.
    """
    filters = UserFilters(limit=request.limit, offset=request.offset)
    filters.add_sort(request.sort_by, request.sort)
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
    Пример add_sort(): API-схема (ApiUserSortBy) → доменные фильтры (UserFilters с UserSortField).

    В запросе приходит enum из API-схемы; добавляем сортировку в доменные фильтры без явного маппинга.
    """
    print("\n--- add_sort(): API-схема → доменные фильтры ---")
    request = QueryRequestApiSortBy(
        sort_by=ApiUserSortBy.NAME,
        sort=Order.DESC,
        limit=5,
    )
    filters = request_to_filters_from_value(request)

    filters.add_sort(
        request.sort_by,
        request.sort,
    )

    print(f"  has_sort() = {filters.has_sort()}")

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
