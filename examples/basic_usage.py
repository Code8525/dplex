"""Basic usage example"""

import asyncio
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from dataplex import BaseRepository, BaseService, FilterSchema


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)


@dataclass
class UserCreateSchema:
    name: str
    email: str
    is_active: bool = True


@dataclass
class UserFilterSchema(FilterSchema):
    name: str | None = None
    is_active: bool | None = None


async def main():
    # Create engine and session
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        # Create repository
        user_repo = BaseRepository(User, session)

        # Create user
        user_data = UserCreateSchema(name="John Doe", email="john@example.com")
        # user = await user_repo.create(user_data)

        # Get all users
        users = await user_repo.get_all()
        print(f"Found {len(users)} users")


if __name__ == "__main__":
    asyncio.run(main())
