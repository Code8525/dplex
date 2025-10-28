from __future__ import annotations
import uuid
from datetime import datetime

from enum import StrEnum

from pydantic import BaseModel, Field
from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from dplex import DPFilters, DPRepo, DPService
from dplex.internal.filters import UUIDFilter, StringFilter, DateTimeFilter
from dplex.internal.sort import Sort, Order, NullsPlacement


# === dplex базис (у вас уже есть) ===


# ===================== 1) Модель =====================
class Base(DeclarativeBase): ...


class User(Base):
    __tablename__ = "users"

    # ⚠️ Имя колонки совпадает с enum-значением сортировки (см. ниже)
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


# ===================== 2) Pydantic-схемы =====================
class UserCreate(BaseModel):
    name: str
    email: str | None = None


class UserUpdate(BaseModel):
    # Используем маркер NULL, чтобы явно обнулить поле (NULL в БД)
    name: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str | None
    created_at: datetime


# ===================== 3) Сортировка и фильтры =====================
class UserSortField(StrEnum):
    # Значения должны совпадать с ИМЕНАМИ колонок модели
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
        super().__init__(
            model=User, session=session, key_type=uuid.UUID, id_field_name="user_id"
        )


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


# ===================== 6) Пример использования =====================
# Пример асинхронного CRUD-потока
async def example_flow(session: AsyncSession) -> None:
    repo = UserRepo(session)
    service = UserService(repo, session)

    # ---- Create
    u = await service.create(UserCreate(name="Иван", email="ivan@example.com"))
    print("Created:", u)

    # ---- Read (list с фильтрами + сортировкой + пагинацией)
    filters = UserFilters(
        email=StringFilter(ends_with="@mail.ru"),
        sort=[  # можно список Sort(...) для multi-sort
            Sort(
                by=UserSortField.CREATED_AT, order=Order.DESC, nulls=NullsPlacement.LAST
            ),
            Sort(by=UserSortField.NAME, order=Order.ASC),
        ],
        limit=50,
        offset=0,
        user_id=UUIDFilter(eq=u.user_id),
    )
    users = await service.get_all(filters)
    print("Found:", users)

    # ---- Update (обнуление email через специальный маркер NULL)
    u2 = await service.update_by_id(
        u.user_id, UserUpdate(email=None)  # ← это поставит email IS NULL в БД
    )
    print("Updated:", u2)

    # ---- Exists / Count
    exists = await service.exists(UserFilters(user_id=UUIDFilter(eq=u.user_id)))
    total = await service.count(UserFilters())
    print("Exists?", exists, "Total:", total)

    # ---- Delete
    deleted = await service.delete_by_id(u.user_id)
    print("Deleted?", deleted)
