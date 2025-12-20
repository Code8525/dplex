# dplex

Enterprise-grade data layer framework for Python с продвинутой системой фильтрации, сортировки и пагинации.

## Описание

dplex — это современный фреймворк для построения слоя работы с данными в Python приложениях. Он предоставляет унифицированный подход к фильтрации, сортировке и пагинации данных, работая поверх SQLAlchemy ORM.

### Основные возможности

- 🔍 **Продвинутая фильтрация** — 11 типов фильтров с множественными операциями
- 📊 **Гибкая сортировка** — множественная сортировка с контролем NULL значений
- 📄 **Пагинация из коробки** — встроенная поддержка limit/offset
- 🎯 **Типобезопасность** — полная поддержка type hints Python 3.9+
- 🏗️ **Архитектурные паттерны** — Repository и Service patterns
- ⚡ **Производительность** — оптимизированные SQL запросы без N+1 проблем

## Установка

```bash
pip install dplex
```

### Требования

- Python 3.9+
- SQLAlchemy 2.0+
- Pydantic 2.0+

## Быстрый старт

### 1. Определите модель SQLAlchemy

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    age: Mapped[int]
    is_active: Mapped[bool]
```

### 2. Создайте схему фильтрации

```python
from enum import StrEnum
from dplex import DPFilters, StringFilter, IntFilter, BooleanFilter

class UserSortField(StrEnum):
    NAME = "name"
    EMAIL = "email"
    AGE = "age"
    CREATED_AT = "created_at"

class UserFilters(DPFilters[UserSortField]):
    name: StringFilter | None = None
    email: StringFilter | None = None
    age: IntFilter | None = None
    is_active: BooleanFilter | None = None
```

### 3. Используйте репозиторий

```python
from sqlalchemy.ext.asyncio import AsyncSession
from dplex import DPRepo, Sort, Order

class UserRepository(DPRepo[User, int]):
    pass

# В вашем коде
async def get_users(session: AsyncSession):
    repo = UserRepository(session, User)
    
    # Создайте фильтры
    filters = UserFilters(
        name=StringFilter(icontains="john"),
        age=IntFilter(gte=18, lte=65),
        is_active=BooleanFilter(eq=True),
        sort=Sort(by=UserSortField.NAME, order=Order.ASC),
        limit=10,
        offset=0
    )
    
    # Получите данные
    users = await repo.get_all(filters=filters)
    return users
```

## Типы фильтров

dplex предоставляет 11 специализированных типов фильтров:

### StringFilter

Фильтрация строковых полей с поддержкой паттернов и регистронезависимого поиска.

```python
from dplex import StringFilter

# Точное совпадение
StringFilter(eq="john@example.com")

# Содержит (регистронезависимо)
StringFilter(icontains="john")

# Начинается с
StringFilter(starts_with="Dr.")

# Заканчивается на
StringFilter(ends_with=".com")

# Список значений
StringFilter(in_=["admin", "moderator"])

# Комбинация условий
StringFilter(
    icontains="john",
    ends_with="@example.com",
    ne="john.blocked@example.com"
)
```

**Доступные операции:**
- `eq`, `ne` — равно/не равно
- `in_`, `not_in` — в списке/не в списке
- `gt`, `gte`, `lt`, `lte` — больше/меньше (лексикографически)
- `contains`, `icontains` — содержит (с учетом регистра/без)
- `startswith`, `istartswith` — начинается с
- `endswith`, `iendswith` — заканчивается на
- `is_null` — NULL проверка

### IntFilter

Фильтрация целочисленных полей.

```python
from dplex import IntFilter

# Диапазон
IntFilter(gte=18, lte=65)

# Список значений
IntFilter(in_=[1, 2, 3, 5, 8])

# Неравенство
IntFilter(ne=0)
```

**Доступные операции:**
- `eq`, `ne` — равно/не равно
- `in_`, `not_in` — в списке/не в списке
- `gt`, `gte`, `lt`, `lte` — больше/меньше
- `is_null` — NULL проверка

### FloatFilter

Фильтрация чисел с плавающей точкой.

```python
from dplex import FloatFilter

# Диапазон с точностью
FloatFilter(gte=0.0, lt=100.0)

# Точное значение
FloatFilter(eq=3.14159)
```

**Операции:** аналогичны IntFilter

### DecimalFilter

Фильтрация точных десятичных чисел (Decimal).

```python
from decimal import Decimal
from dplex import DecimalFilter

# Для финансовых расчетов
DecimalFilter(gte=Decimal("0.01"), lte=Decimal("999999.99"))
```

**Операции:** аналогичны IntFilter

### DateTimeFilter

Фильтрация даты и времени.

```python
from datetime import datetime
from dplex import DateTimeFilter

# Диапазон дат
DateTimeFilter(
    gte=datetime(2024, 1, 1),
    lt=datetime(2024, 12, 31)
)

# После определенной даты
DateTimeFilter(gt=datetime(2024, 6, 1))
```

**Операции:** `eq`, `ne`, `in_`, `not_in`, `gt`, `gte`, `lt`, `lte`, `is_null`

### DateFilter

Фильтрация только даты (без времени).

```python
from datetime import date
from dplex import DateFilter

# Конкретная дата
DateFilter(eq=date(2024, 1, 1))

# Диапазон
DateFilter(gte=date(2024, 1, 1), lte=date(2024, 12, 31))
```

**Операции:** аналогичны DateTimeFilter

### TimeFilter

Фильтрация только времени.

```python
from datetime import time
from dplex import TimeFilter

# Рабочие часы
TimeFilter(gte=time(9, 0), lt=time(18, 0))
```

**Операции:** аналогичны DateTimeFilter

### TimestampFilter

Фильтрация Unix timestamp (целые числа).

```python
from dplex import TimestampFilter

# После определенного момента
TimestampFilter(gte=1704067200)  # 2024-01-01 00:00:00
```

**Операции:** аналогичны IntFilter

### BooleanFilter

Фильтрация булевых значений.

```python
from dplex import BooleanFilter

# Только активные
BooleanFilter(eq=True)

# NULL проверка
BooleanFilter(is_null=False)
```

**Операции:** `eq`, `ne`, `is_null`

### EnumFilter

Фильтрация enum полей.

```python
from enum import Enum
from dplex import EnumFilter

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# Конкретная роль
EnumFilter(eq=UserRole.ADMIN)

# Несколько ролей
EnumFilter(in_=[UserRole.ADMIN, UserRole.USER])
```

**Операции:** `eq`, `ne`, `in_`, `not_in`, `is_null`

### UUIDFilter

Фильтрация UUID полей.

```python
import uuid
from dplex import UUIDFilter

# Конкретный UUID
UUIDFilter(eq=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"))

# Список UUID
UUIDFilter(in_=[
    uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
    uuid.UUID("223e4567-e89b-12d3-a456-426614174000")
])
```

**Операции:** `eq`, `ne`, `in_`, `not_in`, `is_null`

## Сортировка

### Простая сортировка

```python
from dplex import Sort, Order

# По возрастанию
filters = UserFilters(
    sort=Sort(by=UserSortField.NAME, order=Order.ASC)
)

# По убыванию
filters = UserFilters(
    sort=Sort(by=UserSortField.AGE, order=Order.DESC)
)
```

### Множественная сортировка

```python
# Сначала по возрасту (DESC), затем по имени (ASC)
filters = UserFilters(
    sort=[
        Sort(by=UserSortField.AGE, order=Order.DESC),
        Sort(by=UserSortField.NAME, order=Order.ASC)
    ]
)
```

### Обработка NULL значений

```python
from dplex import NullsPlacement

# NULL значения в начале
filters = UserFilters(
    sort=Sort(
        by=UserSortField.NAME,
        order=Order.ASC,
        nulls=NullsPlacement.FIRST
    )
)

# NULL значения в конце
filters = UserFilters(
    sort=Sort(
        by=UserSortField.NAME,
        order=Order.ASC,
        nulls=NullsPlacement.LAST
    )
)
```

## Пагинация

```python
# Первая страница (10 записей)
filters = UserFilters(limit=10, offset=0)

# Вторая страница
filters = UserFilters(limit=10, offset=10)

# Третья страница
filters = UserFilters(limit=10, offset=20)
```

## DPRepo — Repository Pattern

`DPRepo` предоставляет базовый функционал для работы с моделями через Repository Pattern.

### Создание репозитория

```python
from dplex import DPRepo
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository(DPRepo[User, int]):
    """Репозиторий для работы с пользователями"""
    pass

# Использование
async def example(session: AsyncSession):
    repo = UserRepository(session, User)
```

### Основные методы

#### get_all() — получить список записей

```python
# Все записи
users = await repo.get_all()

# С фильтрами
users = await repo.get_all(filters=UserFilters(
    is_active=BooleanFilter(eq=True),
    limit=10
))
```

#### get_by_id() — получить запись по ID

```python
user = await repo.get_by_id(user_id=1)
if user is None:
    # Запись не найдена
    pass
```

#### create() — создать запись

```python
new_user = await repo.create(
    name="John Doe",
    email="john@example.com",
    age=30
)
```

#### update() — обновить запись

```python
updated_user = await repo.update(
    item_id=1,
    name="Jane Doe",
    age=31
)
```

#### delete() — удалить запись

```python
deleted_user = await repo.delete(item_id=1)
```

#### exists() — проверить существование

```python
if await repo.exists(item_id=1):
    print("Пользователь существует")
```

#### count() — подсчитать записи

```python
# Всего записей
total = await repo.count()

# С фильтрами
active_count = await repo.count(filters=UserFilters(
    is_active=BooleanFilter(eq=True)
))
```

## DPService — Service Pattern

`DPService` расширяет функционал репозитория, добавляя бизнес-логику и работу с Pydantic схемами.

### Создание сервиса

```python
from dplex import DPService
from pydantic import BaseModel

# Pydantic схемы
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    email: str
    age: int

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    age: int | None = None

# Сервис
class UserService(DPService[User, int, UserResponse, UserCreate, UserUpdate, UserFilters]):
    """Сервис для работы с пользователями"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=User,
            response_schema=UserResponse
        )

# Использование
async def example(session: AsyncSession):
    service = UserService(session)
```

### Основные методы

#### get_all() — получить список с преобразованием в схемы

```python
users: list[UserResponse] = await service.get_all(
    filters=UserFilters(
        is_active=BooleanFilter(eq=True),
        limit=10
    )
)
```

#### get_by_id() — получить одну запись

```python
user: UserResponse | None = await service.get_by_id(user_id=1)
```

#### create() — создать запись из схемы

```python
create_data = UserCreate(
    name="John Doe",
    email="john@example.com",
    age=30
)
new_user: UserResponse = await service.create(create_data)
```

#### update() — обновить запись

```python
update_data = UserUpdate(age=31)
updated_user: UserResponse = await service.update(
    item_id=1,
    update_schema=update_data
)
```

#### delete() — удалить запись

```python
deleted_user: UserResponse = await service.delete(item_id=1)
```

## Продвинутые примеры

### Комплексная фильтрация

```python
filters = UserFilters(
    # Имя содержит "john" (регистронезависимо)
    name=StringFilter(icontains="john"),
    
    # Email в домене example.com
    email=StringFilter(endswith="@example.com"),
    
    # Возраст от 18 до 65
    age=IntFilter(gte=18, lte=65),
    
    # Только активные
    is_active=BooleanFilter(eq=True),
    
    # Сортировка: сначала по возрасту (DESC), затем по имени (ASC)
    sort=[
        Sort(by=UserSortField.AGE, order=Order.DESC),
        Sort(by=UserSortField.NAME, order=Order.ASC)
    ],
    
    # Пагинация
    limit=20,
    offset=0
)

users = await repo.get_all(filters=filters)
```

### Работа с фильтрами

```python
# Создать фильтры
filters = UserFilters(
    name=StringFilter(icontains="john"),
    age=IntFilter(gte=18)
)

# Проверить наличие фильтров
if filters.has_filters():
    print(f"Активных фильтров: {filters.get_filter_count()}")

# Получить активные фильтры
active = filters.get_active_filters()
print(active)  # {'name': StringFilter(...), 'age': IntFilter(...)}

# Получить имена полей с фильтрами
fields = filters.get_filter_fields()
print(fields)  # ['name', 'age']

# Сводка по фильтрам
summary = filters.get_filter_summary()
print(summary)  # {'name': 1, 'age': 1}

# Очистить фильтры
filters.clear_filters()
print(filters.has_filters())  # False
```

### Кастомные фильтры

Кастомные фильтры позволяют создавать фильтры для полей, которых нет в модели, но требуют специальной обработки (например, поиск по нескольким полям одновременно).

#### Базовое использование

```python
from dplex import DPService, StringFilter

class UserFilterableFields(DPFilters[UserSortField]):
    name: StringFilter | None = None
    email: StringFilter | None = None
    # Кастомный фильтр - поля 'query' нет в модели User
    query: StringFilter | None = None

class UserService(DPService[...]):
    def apply_custom_filters(self, query_builder, filter_data):
        """Обработка кастомного фильтра 'query'"""
        # Получаем кастомные фильтры через helper метод
        custom_filters = self._get_custom_filters(filter_data)
        
        if 'query' not in custom_filters:
            return query_builder
        
        query_filter = custom_filters['query']
        search_columns = [User.name, User.email, User.bio]
        
        # Используем helper метод для обработки операций StringFilter
        if hasattr(query_filter, 'icontains') and query_filter.icontains:
            query_builder = self._apply_string_filter_operation(
                query_builder, query_filter, 'icontains', search_columns, case_sensitive=False
            )
        elif hasattr(query_filter, 'contains') and query_filter.contains:
            query_builder = self._apply_string_filter_operation(
                query_builder, query_filter, 'contains', search_columns, case_sensitive=True
            )
        
        return query_builder

# Использование
filters = UserFilterableFields(
    query=StringFilter(icontains="john"),  # Поиск по всем полям
    age=IntFilter(gte=18)  # Комбинация с обычным фильтром
)
users = await service.get_all(filters)
```

#### Ручная обработка (без helper методов)

```python
from sqlalchemy import or_

class UserService(DPService[...]):
    def apply_custom_filters(self, query_builder, filter_data):
        custom_filters = self._get_custom_filters(filter_data)
        
        if 'query' in custom_filters:
            query_filter = custom_filters['query']
            if hasattr(query_filter, 'icontains') and query_filter.icontains:
                search_term = query_filter.icontains
                condition = or_(
                    User.name.ilike(f'%{search_term}%'),
                    User.email.ilike(f'%{search_term}%'),
                    User.bio.ilike(f'%{search_term}%')
                )
                query_builder = query_builder.where(condition)
        
        return query_builder
```

**Особенности кастомных фильтров:**
- Поля в схеме фильтрации, которых нет в модели
- Обрабатываются через метод `apply_custom_filters()` в сервисе
- Можно комбинировать с обычными фильтрами
- Поддерживают все операции фильтрации (icontains, contains, eq и т.д.)
- Гибкая логика (например, поиск по нескольким полям через OR)

**Helper методы:**
- `_get_custom_filters(filter_data)` - получить кастомные фильтры
- `_apply_string_filter_operation(query_builder, filter, operation, columns, case_sensitive)` - применить операцию StringFilter к нескольким колонкам

### Информация о пагинации

```python
filters = UserFilters(limit=10, offset=20)

# Проверить наличие пагинации
if filters.has_pagination():
    info = filters.get_pagination_info()
    print(info)  # {'limit': 10, 'offset': 20}
```

### Проверка сортировки

```python
filters = UserFilters(
    sort=Sort(by=UserSortField.NAME, order=Order.ASC)
)

if filters.has_sort():
    print("Сортировка установлена")
```

## Архитектурные паттерны

### Repository Pattern

Репозиторий инкапсулирует логику доступа к данным, предоставляя коллекцию-подобный интерфейс.

```python
class UserRepository(DPRepo[User, int]):
    async def get_active_users(self) -> list[User]:
        """Кастомный метод репозитория"""
        return await self.get_all(
            filters=UserFilters(
                is_active=BooleanFilter(eq=True)
            )
        )
    
    async def get_by_email(self, email: str) -> User | None:
        """Найти пользователя по email"""
        users = await self.get_all(
            filters=UserFilters(
                email=StringFilter(eq=email),
                limit=1
            )
        )
        return users[0] if users else None
```

### Service Pattern

Сервис содержит бизнес-логику и работает с Pydantic схемами для валидации.

```python
class UserService(DPService[User, int, UserResponse, UserCreate, UserUpdate, UserFilters]):
    async def register_user(self, data: UserCreate) -> UserResponse:
        """Регистрация нового пользователя с дополнительной логикой"""
        # Проверка уникальности email
        existing = await self.repo.get_all(
            filters=UserFilters(
                email=StringFilter(eq=data.email),
                limit=1
            )
        )
        if existing:
            raise ValueError("Email уже используется")
        
        # Создание пользователя
        return await self.create(data)
    
    async def deactivate_user(self, user_id: int) -> UserResponse:
        """Деактивация пользователя"""
        return await self.update(
            item_id=user_id,
            update_schema=UserUpdate(is_active=False)
        )
```

## Соглашения по кодированию

dplex следует современным практикам Python:

### Типы данных

```python
# ✅ Правильно — встроенные типы Python 3.9+
users: list[User] | None = None
data: dict[str, int] = {}

# ❌ Неправильно — старый синтаксис typing
from typing import List, Dict, Optional
users: Optional[List[User]] = None
data: Dict[str, int] = {}
```



## Лицензия

MIT License

## Поддержка

- Документация: [в разработке]
- Issues: [GitHub Issues]
- Обсуждения: [GitHub Discussions]

## Changelog

### 0.1.0 (текущая версия)

- Начальный релиз
- Поддержка 11 типов фильтров
- Repository и Service patterns
- Множественная сортировка с контролем NULL
- Встроенная пагинация
- Полная типобезопасность

---

