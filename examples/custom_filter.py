"""
Пример использования кастомных фильтров

Демонстрирует работу с кастомными фильтрами, которые не соответствуют
полям модели. WordsFilter теперь поддерживает указание колонок прямо в фильтре,
и обработка выполняется автоматически через стандартную логику FilterApplier.
"""

import asyncio
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import String, Integer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

from dplex import DPService, Sort, Order, WordsFilter
from dplex.dp_repo import DPRepo
from dplex.dp_filters import DPFilters
from dplex.internal.filters import StringFilter, IntFilter, DateTimeFilter


# ==================== МОДЕЛИ И СХЕМЫ ====================


# SQLAlchemy модель
class Base(DeclarativeBase):
    pass


class User(Base):
    """Модель пользователя"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    age: Mapped[int] = mapped_column(Integer)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(insert_default=datetime.now)


# Enum для сортировки
class UserSortField(StrEnum):
    """Поля для сортировки пользователей"""

    ID = "id"
    NAME = "name"
    EMAIL = "email"
    AGE = "age"
    CREATED_AT = "created_at"


# Pydantic схемы
class UserCreate(BaseModel):
    """Схема для создания пользователя"""

    name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(ge=0, le=150)
    bio: str | None = None


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""

    id: int
    name: str
    email: str | None
    age: int
    bio: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""

    name: str | None = None
    email: str | None = None
    age: int | None = None
    bio: str | None = None


class UserFilters(DPFilters[UserSortField]):
    """Схема для фильтрации пользователей"""

    name: StringFilter | None = None
    email: StringFilter | None = None
    age: IntFilter | None = None
    created_at: DateTimeFilter | None = None
    # Кастомный фильтр - поля 'query' нет в модели User
    # WordsFilter автоматически разбивает строку на слова
    # Колонки для поиска указываются при создании фильтра
    query: WordsFilter | None = None


# Сервис с обработкой кастомного фильтра
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
    """Сервис для работы с пользователями с поддержкой кастомного фильтра 'query'"""

    # Теперь обработка WordsFilter выполняется автоматически через FilterApplier
    # если колонки указаны в самом фильтре. Метод apply_custom_filters больше не нужен.


# ==================== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ====================


async def example_custom_filter_basic(service: UserService) -> None:
    """
    Пример: Базовое использование кастомного фильтра 'query'

    Использует: get_all() с кастомным фильтром
    """
    print("\n=== CUSTOM FILTER: Базовый поиск ===")

    # Поиск по одному слову (колонки указаны в фильтре)
    filters = UserFilters(
        query=WordsFilter("john", columns=[User.name, User.email, User.bio])
    )
    users = await service.get_all(filters)

    print(f"✓ Найдено пользователей по запросу 'john': {len(users)}")
    for user in users:
        print(f"  - {user.name} ({user.email}) - {user.bio}")

    # Поиск по нескольким словам (колонки указаны в фильтре)
    print("\n=== CUSTOM FILTER: Поиск по нескольким словам ===")
    filters = UserFilters(
        query=WordsFilter("john developer", columns=[User.name, User.email, User.bio])
    )
    users = await service.get_all(filters)

    print(f"✓ Найдено пользователей по запросу 'john developer': {len(users)}")
    for user in users:
        print(f"  - {user.name} ({user.email}) - {user.bio}")


async def example_custom_filter_combined(service: UserService) -> None:
    """
    Пример: Комбинация кастомного фильтра с обычными фильтрами

    Использует: get_all() с кастомным и обычными фильтрами
    """
    print("\n=== CUSTOM FILTER: Комбинация фильтров ===")

    # Поиск по нескольким словам + фильтр по возрасту (колонки указаны в фильтре)
    filters = UserFilters(
        query=WordsFilter(
            "python developer", columns=[User.name, User.email, User.bio]
        ),
        age=IntFilter(gte=25),
    )
    users = await service.get_all(filters)

    print(f"✓ Найдено Python разработчиков 25+: {len(users)}")
    for user in users:
        print(f"  - {user.name}, возраст: {user.age}, bio: {user.bio}")


async def example_custom_filter_multiple_words(service: UserService) -> None:
    """
    Пример: Поиск по нескольким словам

    Использует: get_all() с несколькими словами в запросе
    """
    print("\n=== CUSTOM FILTER: Поиск по нескольким словам ===")

    # Поиск по нескольким словам - все слова должны быть найдены (колонки указаны в фильтре)
    filters = UserFilters(
        query=WordsFilter("alice gmail", columns=[User.name, User.email, User.bio])
    )
    users = await service.get_all(filters)

    print(f"✓ Найдено пользователей с 'alice' и 'gmail': {len(users)}")
    for user in users:
        print(f"  - {user.name} ({user.email}) - {user.bio}")


async def example_custom_filter_with_sort(service: UserService) -> None:
    """
    Пример: Кастомный фильтр с сортировкой

    Использует: get_all() с query и сортировкой
    """
    print("\n=== CUSTOM FILTER: С сортировкой ===")

    filters = UserFilters(
        query=WordsFilter("gmail", columns=[User.name, User.email, User.bio]),
        sort=Sort(by=UserSortField.NAME, order=Order.ASC),
    )
    users = await service.get_all(filters)

    print(f"✓ Найдено пользователей с Gmail (отсортировано по имени): {len(users)}")
    for user in users:
        print(f"  - {user.name} ({user.email})")


async def example_custom_filter_count(service: UserService) -> None:
    """
    Пример: Подсчет с кастомным фильтром

    Использует: count() с кастомным фильтром
    """
    print("\n=== CUSTOM FILTER: Подсчет ===")

    filters = UserFilters(
        query=WordsFilter("python", columns=[User.name, User.email, User.bio])
    )
    count = await service.count(filters)

    print(f"✓ Найдено записей с 'python': {count}")


# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================


async def init_database(engine) -> None:
    """Создать все таблицы в БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ База данных инициализирована")


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================


async def run_examples() -> None:
    """Запустить все примеры"""

    # Создание движка и сессии
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    # Инициализация БД
    await init_database(engine)

    # Создание фабрики сессий
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        repository = DPRepo(model=User, session=session, key_type=int)
        service = UserService(repository, session, UserResponse)

        # Создаем тестовые данные
        test_users = [
            UserCreate(
                name="John Doe",
                email="john.doe@example.com",
                age=30,
                bio="Python Developer",
            ),
            UserCreate(
                name="Jane Smith",
                email="jane.smith@gmail.com",
                age=25,
                bio="JavaScript Developer",
            ),
            UserCreate(
                name="Bob Johnson",
                email="bob.johnson@example.com",
                age=35,
                bio="Full Stack Developer",
            ),
            UserCreate(
                name="Alice Brown",
                email="alice.brown@gmail.com",
                age=28,
                bio="Data Scientist",
            ),
        ]

        created_users = await service.create_bulk(test_users)
        await service.session.commit()

        print("=" * 70)
        print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ КАСТОМНЫХ ФИЛЬТРОВ")
        print("=" * 70)
        print(f"\n✓ Создано {len(created_users)} тестовых пользователей")

        # Запускаем примеры
        await example_custom_filter_basic(service)
        await example_custom_filter_combined(service)
        await example_custom_filter_multiple_words(service)
        await example_custom_filter_with_sort(service)
        await example_custom_filter_count(service)

        print("\n" + "=" * 70)
        print("✓ ВСЕ ПРИМЕРЫ УСПЕШНО ЗАВЕРШЕНЫ")
        print("=" * 70)
        print("\nОСНОВНЫЕ ВОЗМОЖНОСТИ КАСТОМНЫХ ФИЛЬТРОВ:")
        print("  1. Поля в схеме фильтрации, которых нет в модели")
        print("  2. WordsFilter с указанием колонок обрабатывается автоматически")
        print("  3. Можно комбинировать с обычными фильтрами")
        print("  4. Разбивка строки на слова и поиск каждого слова в разных колонках")
        print("  5. AND между словами (все слова должны быть найдены)")
        print("  6. OR между колонками (слово может быть в любой колонке)")
        print("  7. Колонки указываются прямо в WordsFilter при создании")


if __name__ == "__main__":
    asyncio.run(run_examples())
