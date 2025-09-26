#!/usr/bin/env python3
"""
Скрипт для создания структуры проекта dplex
Запуск: python create_dplex.py
"""

from pathlib import Path
from typing import Dict


def get_file_contents() -> Dict[str, str]:
    """Содержимое файлов для создания"""

    return {
        # === ОСНОВНЫЕ КОНФИГУРАЦИОННЫЕ ФАЙЛЫ ===
        "pyproject.toml": """[tool.poetry]
name = "dplex"
version = "0.1.0"
description = "Enterprise-grade data layer framework for Python"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
homepage = "https://github.com/yourusername/dplex"
repository = "https://github.com/yourusername/dplex"
keywords = ["sqlalchemy", "orm", "repository", "service", "cache", "audit"]

[tool.poetry.dependencies]
python = "^3.9"
sqlalchemy = "^2.0.0"
pydantic = "^2.0.0"
redis = {version = "^5.0.0", optional = true}
fastapi = {version = "^0.104.0", optional = true}
click = {version = "^8.1.0", optional = true}

[tool.poetry.extras]
redis = ["redis"]
fastapi = ["fastapi"]
cli = ["click"]
all = ["redis", "fastapi", "click"]

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.7.0"
mypy = "^1.5.0"

[tool.poetry.scripts]
dplex = "dplex.cli.main:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",
        "README.md": """# dplex

**Enterprise-grade data layer framework for Python**

## Features

🎯 **Type-safe repositories** with fluent query builder
🚀 **Service layer** with business logic encapsulation
🔄 **Advanced filtering** with typed schemas
💾 **Caching** with Redis integration
📝 **Audit logging** for compliance

## Quick Start

```bash
pip install dplex
```

```python
from dplex import BaseRepository, BaseService

# Create repository
user_repo = BaseRepository(User, session)

# Use filters
filters = UserFilterSchema(name="John", is_active=True)
users = await user_repo.get_all(filters)
```

## License

MIT License
""",
        "LICENSE": """MIT License

Copyright (c) 2024 dplex Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
""",
        "CHANGELOG.md": """# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2024-01-01

### Added
- Initial release
- BaseRepository with QueryBuilder
- BaseService with CRUD operations  
- Filter schemas with typed operators
- Basic caching support
- Audit logging
""",
        ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
coverage.xml

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Databases  
*.db
*.sqlite3

# Logs
*.log

# OS
.DS_Store
Thumbs.db
""",
        # === GITHUB WORKFLOWS ===
        ".github/workflows/tests.yml": """name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      uses: snok/install-poetry@v1

    - name: Install dependencies
      run: poetry install --with dev

    - name: Run tests
      run: poetry run pytest --cov=dplex

    - name: Run linting
      run: |
        poetry run black --check dplex/
        poetry run mypy dplex/
""",
        ".github/workflows/publish.yml": """name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"

    - name: Install Poetry
      uses: snok/install-poetry@v1

    - name: Build package
      run: poetry build

    - name: Publish to PyPI
      run: poetry publish
      env:
        POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
""",
        # === ОСНОВНОЙ ПАКЕТ ===
        "dplex/__init__.py": '''"""
dplex - Enterprise-grade data layer framework for Python
"""

__version__ = "0.1.0"

from .repositories import BaseRepository, QueryBuilder
from .services import BaseService
from .filters import FilterSchema

__all__ = [
    "BaseRepository",
    "QueryBuilder", 
    "BaseService",
    "FilterSchema",
]
''',
        "dplex/version.py": '''"""Version information for dplex"""

__version__ = "0.1.0"
''',
        "dplex/exceptions.py": '''"""dplex exceptions"""


class dplexException(Exception):
    """Base dplex exception"""
    pass


class RepositoryError(dplexException):
    """Repository related errors"""
    pass


class ServiceError(dplexException):
    """Service related errors"""
    pass


class FilterError(dplexException):
    """Filter related errors"""
    pass


class CacheError(dplexException):
    """Cache related errors"""
    pass


class AuditError(dplexException):
    """Audit related errors"""
    pass


class ValidationError(dplexException):
    """Validation related errors"""
    pass
''',
        "dplex/types.py": '''"""Common types for dplex"""

import uuid
from typing import TypeVar, Union

from sqlalchemy.orm import DeclarativeBase

# Generic types
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
KeyType = TypeVar("KeyType", int, str, uuid.UUID)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
FilterSchemaType = TypeVar("FilterSchemaType")

# Union types for common key types
AnyKeyType = Union[int, str, uuid.UUID]
''',
        # === REPOSITORIES ===
        "dplex/repositories/__init__.py": '''"""Repository module"""

from .base import BaseRepository
from .query_builder import QueryBuilder

__all__ = ["BaseRepository", "QueryBuilder"]
''',
        "dplex/repositories/base_repository.py": '''"""Base repository implementation"""

import uuid
from typing import Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ..types import ModelType, KeyType
from .query_builder import QueryBuilder

ModelSchema = TypeVar("ModelSchema", bound=DeclarativeBase)


class BaseRepository(Generic[ModelSchema, KeyType]):
    """Base repository with CRUD operations"""

    def __init__(
        self,
        model: type[ModelSchema],
        session: AsyncSession,
        id_field_name: str = "id"
    ) -> None:
        self.model = model
        self.session = session
        self.id_field_name = id_field_name

    def query(self) -> QueryBuilder[ModelSchema]:
        """Get query builder"""
        return QueryBuilder(self.model, self.session)

    async def get_by_id(self, entity_id: KeyType) -> ModelSchema | None:
        """Get entity by ID"""
        return await self.session.get(self.model, entity_id)

    async def get_all(self) -> list[ModelSchema]:
        """Get all entities"""
        return await self.query().find_all()

    async def create(self, entity: ModelSchema) -> ModelSchema:
        """Create new entity"""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelSchema) -> ModelSchema:
        """Update entity"""
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelSchema) -> None:
        """Delete entity"""
        await self.session.delete(entity)
        await self.session.commit()
''',
        "dplex/repositories/query_builder.py": '''"""Query builder implementation"""

from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelSchema = TypeVar("ModelSchema", bound=DeclarativeBase)


class QueryBuilder(Generic[ModelSchema]):
    """Fluent query builder"""

    def __init__(self, model: type[ModelSchema], session: AsyncSession) -> None:
        self.model = model
        self.session = session
        self._query = select(model)

    def where(self, condition: Any) -> "QueryBuilder[ModelSchema]":
        """Add WHERE condition"""
        self._query = self._query.where(condition)
        return self

    def limit(self, limit: int) -> "QueryBuilder[ModelSchema]":
        """Add LIMIT"""
        self._query = self._query.limit(limit)
        return self

    def offset(self, offset: int) -> "QueryBuilder[ModelSchema]":
        """Add OFFSET"""
        self._query = self._query.offset(offset)
        return self

    async def find_all(self) -> list[ModelSchema]:
        """Execute query and return all results"""
        result = await self.session.execute(self._query)
        return list(result.scalars().all())

    async def find_one(self) -> ModelSchema | None:
        """Execute query and return first result"""
        self._query = self._query.limit(1)
        result = await self.session.execute(self._query)
        return result.scalars().first()
''',
        "dplex/repositories/mixins.py": '''"""Repository mixins"""

from typing import Any


class TimestampMixin:
    """Mixin for automatic timestamps"""
    pass


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    pass
''',
        # === SERVICES ===
        "dplex/services/__init__.py": '''"""Service module"""

from .base import BaseService

__all__ = ["BaseService"]
''',
        "dplex/services/base_repository.py": '''"""Base service implementation"""

from typing import Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.base import BaseRepository
from ..types import ModelType, KeyType, CreateSchemaType, UpdateSchemaType

ModelSchema = TypeVar("ModelSchema")


class BaseService(Generic[ModelSchema, KeyType, CreateSchemaType, UpdateSchemaType]):
    """Base service with business logic"""

    def __init__(
        self,
        repository: BaseRepository[ModelSchema, KeyType],
        session: AsyncSession
    ) -> None:
        self.repository = repository
        self.session = session

    async def get_by_id(self, entity_id: KeyType) -> ModelSchema | None:
        """Get entity by ID"""
        return await self.repository.get_by_id(entity_id)

    async def get_all(self) -> list[ModelSchema]:
        """Get all entities"""
        return await self.repository.get_all()

    async def create(self, create_data: CreateSchemaType) -> ModelSchema:
        """Create new entity"""
        # Convert create_data to entity
        entity_dict = self._prepare_create_data(create_data)
        entity = self.repository.model(**entity_dict)

        return await self.repository.create(entity)

    def _prepare_create_data(self, create_data: CreateSchemaType) -> dict[str, Any]:
        """Prepare data for creation"""
        if hasattr(create_data, 'model_dump'):
            return create_data.model_dump(exclude_none=True)
        elif hasattr(create_data, '__dict__'):
            return create_data.__dict__
        elif isinstance(create_data, dict):
            return create_data
        else:
            raise ValueError(f"Unsupported create_data type: {type(create_data)}")
''',
        "dplex/services/mixins.py": '''"""Service mixins"""


class CacheMixin:
    """Mixin for caching functionality"""
    pass


class AuditMixin:
    """Mixin for audit logging"""
    pass


class ValidationMixin:
    """Mixin for validation"""
    pass
''',
        # === FILTERS ===
        "dplex/filters/__init__.py": '''"""Filter module"""

from .base import FilterSchema
from .operators import NumericFilter, StringFilter, BoolFilter

__all__ = ["FilterSchema", "NumericFilter", "StringFilter", "BoolFilter"]
''',
        "dplex/filters/base_repository.py": '''"""Base filter schema"""

from dataclasses import dataclass
from typing import Any

from ..repositories.query_builder import QueryBuilder


@dataclass
class FilterSchema:
    """Base filter schema"""

    def apply_filters(self, query: QueryBuilder[Any]) -> QueryBuilder[Any]:
        """Apply filters to query builder"""
        return query
''',
        "dplex/filters/operators.py": '''"""Typed filter operators"""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')


@dataclass
class NumericFilter(Generic[T]):
    """Numeric filter operators"""
    eq: T | None = None
    ne: T | None = None
    gt: T | None = None
    gte: T | None = None
    lt: T | None = None
    lte: T | None = None
    in_: list[T] | None = None


@dataclass
class StringFilter:
    """String filter operators"""
    eq: str | None = None
    ne: str | None = None
    like: str | None = None
    ilike: str | None = None
    in_: list[str] | None = None


@dataclass  
class BoolFilter:
    """Boolean filter operators"""
    eq: bool | None = None
''',
        "dplex/filters/schemas.py": '''"""Ready-to-use filter schemas"""

from dataclasses import dataclass
from datetime import datetime

from .base import FilterSchema


@dataclass
class BaseEntityFilterSchema(FilterSchema):
    """Base filter schema for common entities"""

    # Pagination
    page: int = 1
    per_page: int = 10

    # Sorting
    sort_by: str | None = None
    sort_desc: bool = False

    # Common filters
    created_after: datetime | None = None
    created_before: datetime | None = None
    is_active: bool | None = None
''',
        # === ОСТАЛЬНЫЕ МОДУЛИ (заглушки) ===
        "dplex/cache/__init__.py": '''"""Cache module"""

# TODO: Implement caching functionality
''',
        "dplex/audit/__init__.py": '''"""Audit module"""

# TODO: Implement audit logging
''',
        "dplex/soft_delete/__init__.py": '''"""Soft delete module"""

# TODO: Implement soft delete functionality
''',
        "dplex/versioning/__init__.py": '''"""Versioning module"""

# TODO: Implement versioning
''',
        "dplex/validation/__init__.py": '''"""Validation module"""

# TODO: Implement validation rules
''',
        "dplex/migrations/__init__.py": '''"""Migrations module"""

# TODO: Implement schema migrations
''',
        "dplex/metrics/__init__.py": '''"""Metrics module"""

# TODO: Implement performance metrics
''',
        "dplex/integrations/__init__.py": '''"""Integrations module"""

# TODO: Implement framework integrations
''',
        "dplex/cli/__init__.py": '''"""CLI module"""
''',
        "dplex/cli/main.py": '''"""Main CLI entry point"""

import click


@click.group()
@click.version_option(version="0.1.0")
def main():
    """dplex CLI tool"""
    pass


@main.command()
def init():
    """Initialize new dplex project"""
    click.echo("Initializing dplex project...")


if __name__ == "__main__":
    main()
''',
        # === ТЕСТЫ ===
        "tests/__init__.py": "",
        "tests/conftest.py": '''"""Pytest configuration"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


@pytest.fixture
async def async_session():
    """Create async session for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
''',
        "tests/test_repositories/__init__.py": "",
        "tests/test_services/__init__.py": "",
        "tests/test_filters/__init__.py": "",
        # === ПРИМЕРЫ ===
        "examples/basic_usage.py": '''"""Basic usage example"""

import asyncio
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from dplex import BaseRepository, BaseService, FilterSchema


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
''',
        "examples/fastapi_integration.py": '''"""FastAPI integration example"""

from fastapi import FastAPI, Depends
from dplex import BaseRepository, BaseService

app = FastAPI()

# TODO: Add FastAPI integration example
''',
        # === ДОКУМЕНТАЦИЯ ===
        "docs/index.md": """# dplex Documentation

Welcome to dplex - Enterprise-grade data layer framework for Python.

## Features

- Type-safe repositories
- Service layer architecture  
- Advanced filtering
- Caching support
- Audit logging

## Quick Start

See [Quick Start Guide](quickstart.md) for getting started.
""",
        "docs/quickstart.md": """# Quick Start

## Installation

```bash
pip install dplex
```

## Basic Usage

```python
from dplex import BaseRepository

# Create repository
repo = BaseRepository(User, session)

# Get all users
users = await repo.get_all()
```

## Next Steps

- Check out [API Reference](api/)
- See [Examples](examples/)
""",
    }


def create_directory_structure():
    """Создает структуру директорий"""

    directories = [
        # Основные директории
        ".github/workflows",
        "docs/api",
        "docs/examples",
        "examples",
        "tests/test_repositories",
        "tests/test_services",
        "tests/test_filters",
        "tests/test_cache",
        "tests/test_audit",
        "tests/test_migrations",
        "tests/test_integration",
        "benchmarks",
        # Основной пакет
        "dplex",
        "dplex/repositories",
        "dplex/services",
        "dplex/filters",
        "dplex/cache",
        "dplex/audit",
        "dplex/soft_delete",
        "dplex/versioning",
        "dplex/validation",
        "dplex/migrations",
        "dplex/metrics",
        "dplex/integrations/fastapi",
        "dplex/integrations/django/management",
        "dplex/integrations/flask",
        "dplex/integrations/pydantic",
        "dplex/cli",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Создана директория: {directory}")


def create_files():
    """Создает файлы с содержимым"""

    file_contents = get_file_contents()

    for file_path, content in file_contents.items():
        # Создаем родительскую директорию если не существует
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Записываем содержимое
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Создан файл: {file_path}")


def create_empty_files():
    """Создает пустые __init__.py файлы"""

    init_files = [
        # Дополнительные __init__.py файлы
        "dplex/cache/redis.py",
        "dplex/cache/memory.py",
        "dplex/cache/decorators.py",
        "dplex/cache/strategies.py",
        "dplex/audit/models.py",
        "dplex/audit/service.py",
        "dplex/audit/mixins.py",
        "dplex/audit/context.py",
        "dplex/soft_delete/mixins.py",
        "dplex/soft_delete/managers.py",
        "dplex/versioning/models.py",
        "dplex/versioning/mixins.py",
        "dplex/versioning/strategies.py",
        "dplex/validation/rules.py",
        "dplex/validation/validators.py",
        "dplex/validation/decorators.py",
        "dplex/migrations/manager.py",
        "dplex/migrations/generator.py",
        "dplex/migrations/runner.py",
        "dplex/metrics/collectors.py",
        "dplex/metrics/exporters.py",
        "dplex/metrics/decorators.py",
        "dplex/integrations/fastapi/dependencies.py",
        "dplex/integrations/fastapi/filters.py",
        "dplex/integrations/fastapi/middleware.py",
        "dplex/integrations/django/management/commands/__init__.py",
        "dplex/integrations/flask/__init__.py",
        "dplex/integrations/pydantic/filters.py",
        "dplex/cli/migrate.py",
        "dplex/cli/generate.py",
        "dplex/cli/benchmark.py",
        "benchmarks/query_performance.py",
        "benchmarks/cache_performance.py",
        "examples/complex_filtering.py",
        "examples/enterprise_example.py",
        "docs/api/__init__.py",
    ]

    for file_path in init_files:
        # Создаем родительскую директорию если не существует
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Создаем пустой файл с комментарием TODO
        content = f'"""TODO: Implement {Path(file_path).stem} functionality"""\n'

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"📝 Создан файл-заглушка: {file_path}")


def main():
    """Основная функция создания проекта"""

    print("🚀 Создание структуры проекта dplex...")
    print("=" * 50)

    # Создаем директории
    print("\n📁 Создание директорий...")
    create_directory_structure()

    # Создаем файлы с содержимым
    print("\n📝 Создание основных файлов...")
    create_files()

    # Создаем пустые файлы-заглушки
    print("\n📄 Создание файлов-заглушек...")
    create_empty_files()

    print("\n" + "=" * 50)
    print("✅ Проект dplex успешно создан!")
    print("\nСледующие шаги:")
    print("1. cd dplex")
    print("2. poetry install")
    print("3. poetry run pytest")
    print("4. poetry run dplex --help")
    print("\n🎉 Удачной разработки!")


if __name__ == "__main__":
    main()
