from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from sqlalchemy import String, DateTime
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from dplex import (
    DPRepo,
    DPService,
    DPFilters,
    Sort,
    Order,
    StringFilter,
    UUIDFilter,
    DateTimeFilter,
)


# ===================== 1) SQLAlchemy модель =====================
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=datetime.now,
        default=datetime.now,
    )


# ===================== 2) Pydantic-схемы =====================
class UserCreate(BaseModel):
    name: str
    email: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    email: str | None
    created_at: datetime


# ===================== 3) Enum сортировки и фильтры =====================
class UserSortField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


class UserFilters(DPFilters[UserSortField]):
    user_id: UUIDFilter | None = None
    name: StringFilter | None = None
    email: StringFilter | None = None
    created_at: DateTimeFilter | None = None


# ===================== 4) Репозиторий =====================
class UserRepo(DPRepo[User, uuid.UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(
            model=User, session=session, id_field_name="user_id"
        )


# ===================== 5) Сервис =====================
class UserService(
    DPService[
        User,
        uuid.UUID,
        UserCreate,
        UserUpdate,
        UserResponse,
        UserFilters,
        UserSortField,
    ]
):
    def __init__(self, repo: UserRepo, session: AsyncSession):
        super().__init__(repository=repo, session=session, response_schema=UserResponse)


# ===================== 6) Полный пример использования =====================
async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with Session() as session:
        service = UserService(UserRepo(session), session)

        print("\n=== CREATE ===")
        u1 = await service.create(UserCreate(name="Alice", email="alice@mail.com"))
        u2 = await service.create(UserCreate(name="Bob", email=None))
        print(u1)
        print(u2)

        print("\n=== READ + FILTER + SORT ===")
        users = await service.get_all(
            UserFilters(
                email=StringFilter(icontains="mail"),
                sort=[Sort(by=UserSortField.CREATED_AT, order=Order.DESC)],
            )
        )
        print(users)

        print("\n=== UPDATE: изменить name ===")
        await service.update_by_id(u1.user_id, UserUpdate(name="Alice Updated"))
        updated = await service.get_by_id(u1.user_id)
        print(updated)

        print("\n=== UPDATE: установить email = NULL ===")
        await service.update_by_id(u1.user_id, UserUpdate(email=None))
        updated = await service.get_by_id(u1.user_id)
        print(updated)

        print("\n=== BULK UPDATE: всем email = NULL, если имя содержит 'o' ===")
        await service.update(
            UserFilters(name=StringFilter(icontains="o")), UserUpdate(email=None)
        )
        all_users_after_bulk = await service.get_all(UserFilters())
        print(all_users_after_bulk)

        print("\n=== DELETE ===")
        after_delete = await service.get_all(UserFilters())
        print(after_delete)
        await service.delete_by_id(u1.user_id)
        after_delete = await service.get_all(UserFilters())
        print(after_delete)
        await service.delete(UserFilters(name=StringFilter(eq="Bob")))
        after_delete = await service.get_all(UserFilters())
        print(after_delete)


if __name__ == "__main__":
    asyncio.run(main())
