"""
Примеры использования всех публичных методов DPService

Демонстрирует работу с базовым сервисом для управления пользователями,
включая использование маркера NULL для установки полей в NULL.
"""

import asyncio
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import String, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

from dplex import NULL  # Импорт маркера NULL
from dplex.types import NullMarker  # Для type hints
from dplex.repositories.repository import DPRepo
from dplex.services.base_filterable_fields import BaseFilterableFields
from dplex.services.dp_service import DPService
from dplex.services.filters import StringFilter, IntFilter, DateTimeFilter
from dplex.services.sort import Sort, SortDirection


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
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
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
    phone: str | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    """
    Схема для обновления пользователя

    Поддерживает маркер NULL для явной установки полей в NULL:
    - Поле не указано -> не обновляется
    - Поле = значение -> обновляется значением
    - Поле = NULL -> устанавливается в NULL (удаляется)
    """

    name: str | NullMarker | None = None
    email: str | NullMarker | None = None
    age: int | NullMarker | None = None
    bio: str | NullMarker | None = None
    phone: str | NullMarker | None = None
    is_active: bool | NullMarker | None = None


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""

    id: int
    name: str
    email: str | None
    age: int
    bio: str | None
    phone: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserFilterableFields(BaseFilterableFields[UserSortField]):
    """Схема для фильтрации пользователей"""

    name: StringFilter | None = None
    email: StringFilter | None = None
    age: IntFilter | None = None
    created_at: DateTimeFilter | None = None


# Сервис
class UserService(
    DPService[
        User,
        int,
        UserCreate,
        UserUpdate,
        UserResponse,
        UserFilterableFields,
        UserSortField,
    ]
):
    """Сервис для работы с пользователями"""

    pass


# ==================== ПРИМЕРЫ СОЗДАНИЯ ====================


async def example_create_single(service: UserService) -> None:
    """
    Пример: Создать одного пользователя

    Использует: create()
    """
    print("\n=== CREATE: Создание одного пользователя ===")

    new_user = UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        age=30,
        bio="Software Developer",
        phone="+1234567890",
        is_active=True,
    )

    created_user = await service.create(new_user)
    await service.session.commit()

    print(f"✓ Создан пользователь:")
    print(f"  ID: {created_user.id}")
    print(f"  Name: {created_user.name}")
    print(f"  Email: {created_user.email}")
    print(f"  Age: {created_user.age}")
    print(f"  Bio: {created_user.bio}")
    print(f"  Phone: {created_user.phone}")
    print(f"  Created at: {created_user.created_at}")


async def example_create_bulk(service: UserService) -> None:
    """
    Пример: Массовое создание пользователей

    Использует: create_bulk()
    """
    print("\n=== CREATE: Массовое создание (bulk) ===")

    bulk_users = [
        UserCreate(
            name="Alice Smith", email="alice@example.com", age=28, bio="Designer"
        ),
        UserCreate(name="Bob Johnson", email="bob@example.com", age=35, bio="Manager"),
        UserCreate(name="Carol White", email="carol@example.com", age=42),
        UserCreate(
            name="David Brown", email="david@example.com", age=29, phone="+1111111111"
        ),
        UserCreate(
            name="Emma Davis",
            email="emma@example.com",
            age=31,
            bio="Teacher",
            phone="+2222222222",
        ),
    ]

    created_users = await service.create_bulk(bulk_users)
    await service.session.commit()

    print(f"✓ Массово создано {len(created_users)} пользователей:")
    for user in created_users:
        print(f"  - ID: {user.id}, Name: {user.name}, Age: {user.age}")


async def example_create_with_gmail(service: UserService) -> None:
    """
    Пример: Создать пользователей с Gmail адресами

    Использует: create_bulk()
    """
    print("\n=== CREATE: Пользователи с Gmail ===")

    gmail_users = [
        UserCreate(name="Ivan Petrov", email="ivan.petrov@gmail.com", age=25),
        UserCreate(name="Maria Sidorova", email="maria.sidorova@gmail.com", age=22),
        UserCreate(name="Alexey Ivanov", email="alexey.ivanov@gmail.com", age=33),
    ]

    created_users = await service.create_bulk(gmail_users)
    await service.session.commit()

    print(f"✓ Создано {len(created_users)} пользователей с Gmail:")
    for user in created_users:
        print(f"  - {user.name} ({user.email})")


# ==================== ПРИМЕРЫ ЧТЕНИЯ ====================


async def example_get_by_id(service: UserService) -> None:
    """
    Пример: Получить пользователя по ID

    Использует: get_by_id()
    """
    print("\n=== READ: Получение по ID ===")

    user = await service.get_by_id(entity_id=1)
    if user:
        print(
            f"✓ Найден пользователь: ID={user.id}, Name={user.name}, Email={user.email}"
        )
    else:
        print("✗ Пользователь с ID=1 не найден")

    user = await service.get_by_id(entity_id=99999)
    if user is None:
        print("✓ Пользователь с ID=99999 не существует (как и ожидалось)")


async def example_get_by_ids(service: UserService) -> None:
    """
    Пример: Получить несколько пользователей по списку ID

    Использует: get_by_ids()
    """
    print("\n=== READ: Получение по нескольким ID ===")

    user_ids = [1, 2, 3, 999, 1000]
    users = await service.get_by_ids(user_ids)

    print(f"Запрошено {len(user_ids)} ID, найдено {len(users)} пользователей:")
    for user in users:
        print(f"  - ID: {user.id}, Name: {user.name}")


async def example_get_all_basic(service: UserService) -> None:
    """
    Пример: Получить всех пользователей без фильтров

    Использует: get_all()
    """
    print("\n=== READ: Все пользователи (без фильтров) ===")

    filters = UserFilterableFields()
    users = await service.get_all(filters)

    print(f"✓ Всего пользователей в БД: {len(users)}")
    print("Первые 5 пользователей:")
    for user in users[:5]:
        print(f"  - {user.name} ({user.email}), возраст: {user.age}")


async def example_get_all_with_filters(service: UserService) -> None:
    """
    Пример: Получить пользователей с фильтрами

    Использует: get_all() с фильтрацией
    """
    print("\n=== READ: Фильтрация пользователей ===")

    # Фильтр: возраст >= 30
    filters = UserFilterableFields(age=IntFilter(gte=30))
    users = await service.get_all(filters)
    print(f"✓ Пользователей 30+: {len(users)}")
    for user in users[:3]:
        print(f"  - {user.name}, возраст: {user.age}")

    # Фильтр: имя содержит "John"
    filters = UserFilterableFields(name=StringFilter(icontains="john"))
    users = await service.get_all(filters)
    print(f"\n✓ Пользователей с 'john' в имени: {len(users)}")
    for user in users:
        print(f"  - {user.name}")


async def example_get_all_with_sort(service: UserService) -> None:
    """
    Пример: Получить пользователей с сортировкой

    Использует: get_all() с сортировкой
    """
    print("\n=== READ: Сортировка ===")

    # Сортировка по возрасту (по убыванию)
    filters = UserFilterableFields(
        sort=Sort(field=UserSortField.AGE, direction=SortDirection.DESC)
    )
    users = await service.get_all(filters)

    print("Пользователи, отсортированные по возрасту (убывание):")
    for user in users[:5]:
        print(f"  - {user.name}: {user.age} лет")

    # Множественная сортировка
    filters = UserFilterableFields(
        sort=[
            Sort(field=UserSortField.AGE, direction=SortDirection.DESC),
            Sort(field=UserSortField.NAME, direction=SortDirection.ASC),
        ]
    )
    users = await service.get_all(filters)

    print("\nПользователи (возраст DESC, имя ASC):")
    for user in users[:5]:
        print(f"  - {user.name}: {user.age} лет")


async def example_get_all_with_pagination(service: UserService) -> None:
    """
    Пример: Получить пользователей с пагинацией

    Использует: get_all() с limit и offset
    """
    print("\n=== READ: Пагинация ===")

    filters = UserFilterableFields(
        limit=5,
        offset=0,
        sort=Sort(field=UserSortField.ID, direction=SortDirection.ASC),
    )
    users = await service.get_all(filters)

    print(f"Первая страница (5 записей): {len(users)} пользователей")
    for user in users:
        print(f"  - ID: {user.id}, Name: {user.name}")

    filters.offset = 5
    users = await service.get_all(filters)

    print(f"\nВторая страница (5 записей): {len(users)} пользователей")
    for user in users:
        print(f"  - ID: {user.id}, Name: {user.name}")


async def example_get_first(service: UserService) -> None:
    """
    Пример: Получить первого пользователя с фильтрами

    Использует: get_first()
    """
    print("\n=== READ: Получение первого ===")

    filters = UserFilterableFields(email=StringFilter(ends_with="@gmail.com"))
    user = await service.get_first(filters)

    if user:
        print(f"✓ Первый пользователь с Gmail: {user.name} ({user.email})")
    else:
        print("✗ Пользователей с Gmail не найдено")


async def example_count(service: UserService) -> None:
    """
    Пример: Подсчитать количество пользователей

    Использует: count()
    """
    print("\n=== COUNT: Подсчет пользователей ===")

    total = await service.count(UserFilterableFields())
    print(f"✓ Всего пользователей: {total}")

    filters = UserFilterableFields(age=IntFilter(gte=18))
    adults = await service.count(filters)
    print(f"✓ Совершеннолетних: {adults}")

    filters = UserFilterableFields(email=StringFilter(ends_with="@gmail.com"))
    gmail_users = await service.count(filters)
    print(f"✓ С Gmail: {gmail_users}")


async def example_exists(service: UserService) -> None:
    """
    Пример: Проверить существование пользователей

    Использует: exists()
    """
    print("\n=== EXISTS: Проверка существования ===")

    filters = UserFilterableFields(name=StringFilter(eq="John Doe"))
    exists = await service.exists(filters)
    print(f"Существует 'John Doe': {exists}")

    filters = UserFilterableFields(age=IntFilter(lt=18))
    exists = await service.exists(filters)
    print(f"Есть несовершеннолетние: {exists}")


async def example_exists_by_id(service: UserService) -> None:
    """
    Пример: Проверить существование по ID

    Использует: exists_by_id()
    """
    print("\n=== EXISTS: Проверка по ID ===")

    exists = await service.exists_by_id(entity_id=1)
    print(f"ID=1 существует: {exists}")

    exists = await service.exists_by_id(entity_id=99999)
    print(f"ID=99999 существует: {exists}")


# ==================== ПРИМЕРЫ ОБНОВЛЕНИЯ ====================


async def example_update_by_id(service: UserService) -> None:
    """
    Пример: Обновить пользователя по ID

    Использует: update_by_id()
    """
    print("\n=== UPDATE: Обновление по ID ===")

    user_id = 1
    update_data = UserUpdate(name="John Updated", age=31)

    updated_user = await service.update_by_id(user_id, update_data)
    await service.session.commit()

    if updated_user:
        print(f"✓ Обновлен пользователь ID={user_id}:")
        print(f"  Name: {updated_user.name}")
        print(f"  Age: {updated_user.age}")
        print(f"  Email: {updated_user.email} (не изменился)")


async def example_update_with_null_marker(service: UserService) -> None:
    """
    Пример: Обновить пользователя с использованием NULL маркера

    Использует: update_by_id() с NULL
    """
    print("\n=== UPDATE: Использование NULL маркера ===")

    user_id = 2

    # Обновить name и установить bio в NULL
    update_data = UserUpdate(name="Alice Updated", bio=NULL)  # Явно устанавливаем NULL

    updated_user = await service.update_by_id(user_id, update_data)
    await service.session.commit()

    if updated_user:
        print(f"✓ Обновлен пользователь ID={user_id}:")
        print(f"  Name: {updated_user.name}")
        print(f"  Bio: {updated_user.bio} (установлено в NULL)")
        print(f"  Email: {updated_user.email} (не тронут)")


async def example_update_multiple_nulls(service: UserService) -> None:
    """
    Пример: Установить несколько полей в NULL

    Использует: update_by_id() с множественными NULL
    """
    print("\n=== UPDATE: Множественная установка NULL ===")

    user_id = 3

    # Очистить email, bio и phone
    update_data = UserUpdate(email=NULL, bio=NULL, phone=NULL)

    updated_user = await service.update_by_id(user_id, update_data)
    await service.session.commit()

    if updated_user:
        print(f"✓ Очищены поля для пользователя ID={user_id}:")
        print(f"  Email: {updated_user.email}")
        print(f"  Bio: {updated_user.bio}")
        print(f"  Phone: {updated_user.phone}")


async def example_update_mixed(service: UserService) -> None:
    """
    Пример: Смешанное обновление (значения + NULL)

    Использует: update_by_id()
    """
    print("\n=== UPDATE: Смешанное обновление ===")

    user_id = 4

    # Обновить name и age, очистить bio
    update_data = UserUpdate(name="David Mixed Update", age=30, bio=NULL)  # Очистить

    updated_user = await service.update_by_id(user_id, update_data)
    await service.session.commit()

    if updated_user:
        print(f"✓ Смешанное обновление для ID={user_id}:")
        print(f"  Name: {updated_user.name} (обновлено)")
        print(f"  Age: {updated_user.age} (обновлено)")
        print(f"  Bio: {updated_user.bio} (NULL)")
        print(f"  Email: {updated_user.email} (не тронут)")


async def example_update_by_ids(service: UserService) -> None:
    """
    Пример: Обновить несколько пользователей

    Использует: update_by_ids()
    """
    print("\n=== UPDATE: Массовое обновление ===")

    user_ids = [5, 6, 7]
    update_data = UserUpdate(is_active=True)

    updated_users = await service.update_by_ids(user_ids, update_data)
    await service.session.commit()

    print(f"✓ Обновлено {len(updated_users)} пользователей:")
    for user in updated_users:
        print(f"  - ID: {user.id}, Active: {user.is_active}")


async def example_update_by_ids_with_null(service: UserService) -> None:
    """
    Пример: Массовое обновление с NULL маркером

    Использует: update_by_ids() с NULL
    """
    print("\n=== UPDATE: Массовое обновление с NULL ===")

    user_ids = [5, 6, 7]

    # Очистить phone у всех
    update_data = UserUpdate(phone=NULL)

    updated_users = await service.update_by_ids(user_ids, update_data)
    await service.session.commit()

    print(f"✓ Очищен phone у {len(updated_users)} пользователей:")
    for user in updated_users:
        print(f"  - ID: {user.id}, Phone: {user.phone}")


async def example_update_by_id_with_fields(service: UserService) -> None:
    """
    Пример: Обновить конкретные поля

    Использует: update_by_id_with_fields()
    """
    print("\n=== UPDATE: Обновление конкретных полей ===")

    user_id = 1

    # Указываем много полей, но обновим только name
    update_data = UserUpdate(
        name="Selective Update", age=99, is_active=False, bio="This will be ignored"
    )

    updated_user = await service.update_by_id_with_fields(
        user_id, update_data, fields_to_update=["name"]  # Только name
    )
    await service.session.commit()

    if updated_user:
        print(f"✓ Обновлено только поле 'name' для ID={user_id}:")
        print(f"  Name: {updated_user.name} (обновлено)")
        print(f"  Age: {updated_user.age} (не изменился)")
        print(f"  Is Active: {updated_user.is_active} (не изменился)")


async def example_update_with_fields_and_null(service: UserService) -> None:
    """
    Пример: Обновить конкретные поля включая NULL

    Использует: update_by_id_with_fields() с NULL
    """
    print("\n=== UPDATE: Конкретные поля с NULL ===")

    user_id = 2

    # Установим в NULL только email, остальное игнорируем
    update_data = UserUpdate(
        name="Will be ignored",
        email=NULL,  # Будет установлен в NULL
        age=999,  # Будет проигнорирован
    )

    updated_user = await service.update_by_id_with_fields(
        user_id, update_data, fields_to_update=["email"]
    )
    await service.session.commit()

    if updated_user:
        print(f"✓ Обновлен только email для ID={user_id}:")
        print(f"  Email: {updated_user.email} (NULL)")
        print(f"  Name: {updated_user.name} (не изменился)")
        print(f"  Age: {updated_user.age} (не изменился)")


# ==================== ПРИМЕРЫ УДАЛЕНИЯ ====================


async def example_delete_by_id(service: UserService) -> None:
    """
    Пример: Удалить пользователя по ID

    Использует: delete_by_id()
    """
    print("\n=== DELETE: Удаление по ID ===")

    # Создать пользователя для удаления
    temp_user = await service.create(
        UserCreate(name="Temp User", email="temp@example.com", age=25)
    )
    await service.session.commit()
    user_id = temp_user.id

    print(f"Создан временный пользователь ID={user_id}")

    deleted = await service.delete_by_id(user_id)
    await service.session.commit()

    if deleted:
        print(f"✓ Пользователь ID={user_id} успешно удален")

    # Повторная попытка
    deleted = await service.delete_by_id(user_id)
    print(f"Повторное удаление: {deleted} (ожидается False)")


async def example_delete_by_ids(service: UserService) -> None:
    """
    Пример: Удалить несколько пользователей

    Использует: delete_by_ids()
    """
    print("\n=== DELETE: Массовое удаление ===")

    # Создать пользователей для удаления
    temp_users = await service.create_bulk(
        [
            UserCreate(name="Temp 1", email="temp1@example.com", age=25),
            UserCreate(name="Temp 2", email="temp2@example.com", age=26),
            UserCreate(name="Temp 3", email="temp3@example.com", age=27),
        ]
    )
    await service.session.commit()

    user_ids = [u.id for u in temp_users]
    print(f"Создано {len(user_ids)} временных пользователей: {user_ids}")

    deleted_count = await service.delete_by_ids(user_ids)
    await service.session.commit()

    print(f"✓ Удалено {deleted_count} пользователей")


# ==================== ПРИМЕРЫ ПАГИНАЦИИ ====================


async def example_paginate(service: UserService) -> None:
    """
    Пример: Пагинация

    Использует: paginate()
    """
    print("\n=== PAGINATE: Постраничная навигация ===")

    page = 1
    per_page = 5

    filters = UserFilterableFields(
        sort=Sort(field=UserSortField.CREATED_AT, direction=SortDirection.DESC)
    )

    users, total_count = await service.paginate(page, per_page, filters)
    total_pages = (total_count + per_page - 1) // per_page

    print(f"Страница {page} из {total_pages}")
    print(f"Всего записей: {total_count}")
    print(f"На текущей странице: {len(users)}")

    for user in users:
        print(f"  - ID: {user.id}, Name: {user.name}")


async def example_paginate_with_filters(service: UserService) -> None:
    """
    Пример: Пагинация с фильтрами

    Использует: paginate() с фильтрацией
    """
    print("\n=== PAGINATE: С фильтрами ===")

    filters = UserFilterableFields(
        age=IntFilter(gte=18),
        sort=Sort(field=UserSortField.AGE, direction=SortDirection.DESC),
    )

    users, total_count = await service.paginate(1, 5, filters)

    print(f"Найдено совершеннолетних: {total_count}")
    print(f"Показано: {len(users)}")

    for user in users:
        print(f"  - {user.name}, возраст: {user.age}")


# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================


async def init_database(engine) -> None:
    """Создать все таблицы в БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ База данных инициализирована")


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================


async def run_all_examples() -> None:
    """Запустить все примеры"""

    # Создание движка и сессии
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Инициализация БД
    await init_database(engine)

    # Создание фабрики сессий
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        repository = DPRepo(model=User, session=session, key_type=int)
        service = UserService(repository, session, UserResponse)

        print("=" * 70)
        print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ DPSERVICE")
        print("=" * 70)

        # ==================== CREATE ====================
        print("\n" + "=" * 70)
        print("РАЗДЕЛ 1: СОЗДАНИЕ (CREATE)")
        print("=" * 70)

        await example_create_single(service)
        await example_create_bulk(service)
        await example_create_with_gmail(service)

        # ==================== READ ====================
        print("\n" + "=" * 70)
        print("РАЗДЕЛ 2: ЧТЕНИЕ (READ)")
        print("=" * 70)

        await example_get_by_id(service)
        await example_get_by_ids(service)
        await example_get_all_basic(service)
        await example_get_all_with_filters(service)
        await example_get_all_with_sort(service)
        await example_get_all_with_pagination(service)
        await example_get_first(service)

        # ==================== COUNT/EXISTS ====================
        print("\n" + "=" * 70)
        print("РАЗДЕЛ 3: ПОДСЧЕТ И ПРОВЕРКА (COUNT/EXISTS)")
        print("=" * 70)

        await example_count(service)
        await example_exists(service)
        await example_exists_by_id(service)

        # ==================== UPDATE ====================
        print("\n" + "=" * 70)
        print("РАЗДЕЛ 4: ОБНОВЛЕНИЕ (UPDATE)")
        print("=" * 70)

        await example_update_by_id(service)
        await example_update_with_null_marker(service)
        await example_update_multiple_nulls(service)
        await example_update_mixed(service)
        await example_update_by_ids(service)
        await example_update_by_ids_with_null(service)
        await example_update_by_id_with_fields(service)
        await example_update_with_fields_and_null(service)

        # ==================== DELETE ====================
        print("\n" + "=" * 70)
        print("РАЗДЕЛ 5: УДАЛЕНИЕ (DELETE)")
        print("=" * 70)

        await example_delete_by_id(service)
        await example_delete_by_ids(service)

        # ==================== PAGINATION ====================
        print("\n" + "=" * 70)
        print("РАЗДЕЛ 6: ПАГИНАЦИЯ (PAGINATE)")
        print("=" * 70)

        await example_paginate(service)
        await example_paginate_with_filters(service)

        print("\n" + "=" * 70)
        print("✓ ВСЕ ПРИМЕРЫ УСПЕШНО ЗАВЕРШЕНЫ")
        print("=" * 70)
        print("\nОСНОВНЫЕ ВОЗМОЖНОСТИ NULL МАРКЕРА:")
        print("  1. Явная установка полей в NULL: field=NULL")
        print("  2. Работает с update_by_id(), update_by_ids()")
        print("  3. Работает с update_by_id_with_fields()")
        print("  4. Отличается от не указанного поля (не обновляется)")
        print("  5. Type-safe с использованием NullMarker в type hints")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
