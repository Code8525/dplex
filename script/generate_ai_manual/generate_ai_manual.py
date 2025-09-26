#!/usr/bin/env python3
"""
Скрипт для генерации инструкции для ИИ ассистентов на основе структуры проекта dplex
Запуск: python generate_ai_manual.py
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """Информация о файле"""

    path: str
    size: int
    functions: List[str]
    classes: List[str]
    imports: List[str]
    docstring: Optional[str]
    complexity_score: int


@dataclass
class ModuleInfo:
    """Информация о модуле"""

    name: str
    path: str
    files: List[FileInfo]
    purpose: str
    dependencies: List[str]


class CodeAnalyzer:
    """Анализатор кода Python"""

    def __init__(self):
        self.ignore_dirs = {
            "__pycache__",
            ".git",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
            ".idea",
            ".vscode",
            "dist",
            "build",
            ".mypy_cache",
            ".coverage",
            "htmlcov",
        }
        self.ignore_files = {"__pycache__", ".pyc", ".pyo", ".pyd", ".so", ".egg-info"}

    def should_ignore(self, path: Path) -> bool:
        """Проверить, нужно ли игнорировать файл/папку"""
        if any(ignore in str(path) for ignore in self.ignore_dirs):
            return True
        if any(path.name.endswith(ignore) for ignore in self.ignore_files):
            return True
        return False

    def extract_python_info(self, file_path: Path) -> FileInfo:
        """Извлечь информацию из Python файла"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Парсим AST
            tree = ast.parse(content)

            # Извлекаем информацию
            functions = []
            classes = []
            imports = []
            docstring = None

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}")

            # Извлекаем docstring модуля
            if (
                isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)
            ):
                docstring = tree.body[0].value.value

            # Простая метрика сложности
            complexity = (
                len(functions) + len(classes) * 2 + len(content.split("\n")) // 10
            )

            return FileInfo(
                path=str(file_path),
                size=len(content),
                functions=functions,
                classes=classes,
                imports=imports,
                docstring=docstring,
                complexity_score=complexity,
            )

        except Exception as e:
            return FileInfo(
                path=str(file_path),
                size=0,
                functions=[],
                classes=[],
                imports=[],
                docstring=f"Error parsing file: {e}",
                complexity_score=0,
            )

    def analyze_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Анализировать директорию"""
        result = {
            "python_files": [],
            "config_files": [],
            "doc_files": [],
            "other_files": [],
            "subdirectories": [],
        }

        if not dir_path.exists() or self.should_ignore(dir_path):
            return result

        try:
            for item in dir_path.iterdir():
                if self.should_ignore(item):
                    continue

                if item.is_file():
                    if item.suffix == ".py":
                        file_info = self.extract_python_info(item)
                        result["python_files"].append(file_info)
                    elif item.suffix in [
                        ".toml",
                        ".yaml",
                        ".yml",
                        ".json",
                        ".cfg",
                        ".ini",
                    ]:
                        result["config_files"].append(str(item))
                    elif item.suffix in [".md", ".rst", ".txt"]:
                        result["doc_files"].append(str(item))
                    else:
                        result["other_files"].append(str(item))
                elif item.is_dir():
                    result["subdirectories"].append(str(item))

        except PermissionError:
            pass

        return result


class AIManualGenerator:
    """Генератор мануала для ИИ ассистентов"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analyzer = CodeAnalyzer()
        self.manual_content = []

    def get_module_purpose(self, module_path: str) -> str:
        """Определить назначение модуля по пути"""
        module_purposes = {
            "repositories": "Слой репозиториев для работы с данными. Содержит BaseRepository, QueryBuilder и миксины для CRUD операций.",
            "services": "Сервисный слой для бизнес-логики. Содержит BaseService и миксины для обработки бизнес-правил.",
            "filters": "Система фильтрации данных. Типизированные фильтры и операторы для построения запросов.",
            "cache": "Модуль кэширования. Redis интеграция, стратегии кэширования, декораторы.",
            "audit": "Система аудита изменений. Логирование всех операций с данными для compliance.",
            "soft_delete": 'Модуль мягкого удаления. Позволяет "удалять" записи без физического удаления.',
            "versioning": "Система версионирования сущностей. Отслеживание изменений и история версий.",
            "validation": "Модуль валидации бизнес-правил. Валидаторы и декораторы для проверки данных.",
            "migrations": "Система миграций схемы БД. Управление изменениями структуры базы данных.",
            "metrics": "Модуль метрик производительности. Сбор и экспорт метрик для мониторинга.",
            "integrations": "Интеграции с фреймворками. FastAPI, Django, Flask и другие интеграции.",
            "cli": "Интерфейс командной строки. CLI команды для работы с dplex.",
            "tests": "Тесты проекта. Unit тесты, интеграционные тесты, фикстуры.",
            "examples": "Примеры использования. Демонстрационный код для пользователей.",
            "docs": "Документация проекта. Руководства, API референс, туториалы.",
            "benchmarks": "Бенчмарки производительности. Тесты скорости и оптимизации.",
        }

        for key, purpose in module_purposes.items():
            if key in module_path.lower():
                return purpose

        return "Общий модуль проекта."

    def analyze_project_structure(self) -> Dict[str, ModuleInfo]:
        """Анализировать структуру всего проекта"""
        modules = {}

        def scan_directory(current_path: Path, module_name: str = ""):
            """Рекурсивно сканировать директорию"""
            dir_analysis = self.analyzer.analyze_directory(current_path)

            if dir_analysis["python_files"] or module_name:
                modules[module_name or str(current_path)] = ModuleInfo(
                    name=module_name or current_path.name,
                    path=str(current_path),
                    files=dir_analysis["python_files"],
                    purpose=self.get_module_purpose(str(current_path)),
                    dependencies=self._extract_dependencies(
                        dir_analysis["python_files"]
                    ),
                )

            # Рекурсивно обрабатываем подпапки
            for subdir in dir_analysis["subdirectories"]:
                subdir_path = Path(subdir)
                submodule_name = (
                    f"{module_name}.{subdir_path.name}"
                    if module_name
                    else subdir_path.name
                )
                scan_directory(subdir_path, submodule_name)

        # Сканируем основную папку проекта
        scan_directory(self.project_root)

        return modules

    def _extract_dependencies(self, files: List[FileInfo]) -> List[str]:
        """Извлечь зависимости из списка файлов"""
        all_imports = set()
        for file_info in files:
            for imp in file_info.imports:
                # Фильтруем только внешние зависимости
                if not imp.startswith(".") and not imp.startswith("dplex"):
                    all_imports.add(imp.split(".")[0])
        return sorted(list(all_imports))

    def generate_manual_header(self) -> str:
        """Сгенерировать заголовок мануала"""
        return f"""# 🤖 dplex AI Assistant Manual

**Автоматически сгенерированный мануал для работы с проектом dplex**

📅 **Дата генерации:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🏗️ **Проект:** dplex - Enterprise-grade data layer framework for Python
📁 **Корневая директория:** {self.project_root.absolute()}

---

## 🎯 Общее описание проекта

**dplex** - это enterprise-фреймворк для создания слоя данных в Python приложениях. 
Фреймворк предоставляет:

- 🏗️ **Архитектурные паттерны:** Repository + Service Layer
- 🔍 **Типизированные фильтры** для сложных запросов  
- 💾 **Кэширование** с Redis интеграцией
- 📝 **Аудит изменений** для compliance
- 🗑️ **Soft Delete** и версионирование
- ✅ **Валидация** бизнес-правил
- 🔄 **Миграции** схемы БД
- 📊 **Метрики** производительности

---

## 📚 Как использовать этот мануал

Этот мануал содержит:

1. **Структуру проекта** - что где находится
2. **API референс** - классы, функции, методы
3. **Паттерны использования** - как правильно работать с кодом
4. **Зависимости** - какие модули от чего зависят
5. **Примеры кода** - готовые сниппеты

При работе с проектом:
- ✅ Изучите структуру модуля перед изменениями
- ✅ Следуйте существующим паттернам
- ✅ Обновите тесты при изменении API
- ✅ Добавьте docstring'и к новым функциям

---
"""

    def generate_module_section(self, module_info: ModuleInfo) -> str:
        """Сгенерировать секцию для модуля"""
        section = f"""## 📦 Модуль: {module_info.name}

**📁 Путь:** `{module_info.path}`  
**🎯 Назначение:** {module_info.purpose}

"""

        if module_info.dependencies:
            section += f"**🔗 Внешние зависимости:** `{'`, `'.join(module_info.dependencies)}`\n\n"

        if not module_info.files:
            section += "📝 *Модуль пока не содержит Python файлов*\n\n"
            return section

        section += "**📊 Статистика:**\n"
        total_functions = sum(len(f.functions) for f in module_info.files)
        total_classes = sum(len(f.classes) for f in module_info.files)
        total_lines = sum(f.size for f in module_info.files)

        section += f"- Файлов: {len(module_info.files)}\n"
        section += f"- Функций: {total_functions}\n"
        section += f"- Классов: {total_classes}\n"
        section += f"- Строк кода: {total_lines}\n\n"

        # Информация по файлам
        for file_info in sorted(
            module_info.files, key=lambda x: x.complexity_score, reverse=True
        ):
            section += self.generate_file_section(file_info)

        return section

    def generate_file_section(self, file_info: FileInfo) -> str:
        """Сгенерировать секцию для файла"""
        file_name = Path(file_info.path).name
        section = f"### 📄 {file_name}\n\n"

        if file_info.docstring:
            section += f"**📖 Описание:** {file_info.docstring[:200]}{'...' if len(file_info.docstring) > 200 else ''}\n\n"

        section += f"**📊 Метрики:** Строк: {file_info.size} | Сложность: {file_info.complexity_score}\n\n"

        if file_info.classes:
            section += "**🏗️ Классы:**\n"
            for cls in file_info.classes:
                section += f"- `{cls}`\n"
            section += "\n"

        if file_info.functions:
            section += "**⚡ Функции:**\n"
            for func in file_info.functions:
                if not func.startswith("_"):  # Показываем только публичные
                    section += f"- `{func}()`\n"
            section += "\n"

        if file_info.imports:
            important_imports = [
                imp for imp in file_info.imports if not imp.startswith(".")
            ][:5]
            if important_imports:
                section += (
                    f"**📦 Основные импорты:** `{'`, `'.join(important_imports)}`\n\n"
                )

        return section

    def generate_architecture_section(self, modules: Dict[str, ModuleInfo]) -> str:
        """Сгенерировать секцию архитектуры"""
        section = """## 🏗️ Архитектура проекта

### Слои архитектуры

```
┌─────────────────────────────────────┐
│             🌐 API Layer             │  ← integrations/
│          (FastAPI, Django)          │
├─────────────────────────────────────┤
│           📋 Service Layer           │  ← services/
│         (Business Logic)            │
├─────────────────────────────────────┤ 
│          🗂️ Repository Layer         │  ← repositories/
│         (Data Access)               │
├─────────────────────────────────────┤
│            🗃️ Data Layer             │  ← SQLAlchemy Models
│           (Database)                │
└─────────────────────────────────────┘

         🔧 Cross-cutting Concerns:
    ├── 🔍 filters/     - Фильтрация данных
    ├── 💾 cache/       - Кэширование  
    ├── 📝 audit/       - Аудит изменений
    ├── ✅ validation/  - Валидация правил
    ├── 📊 metrics/     - Метрики
    └── 🔄 migrations/  - Миграции БД
```

### Ключевые компоненты

"""

        # Основные компоненты
        key_modules = ["repositories", "services", "filters", "cache", "audit"]
        for module_name, module_info in modules.items():
            if any(key in module_name.lower() for key in key_modules):
                section += f"**{module_info.name}:** {module_info.purpose}\n\n"

        section += """### Паттерны использования

```python
# 1. Создание Repository
repo = BaseRepository(User, session)

# 2. Создание Service  
service = UserService(repo, session)

# 3. Использование фильтров
filters = UserFilterSchema(name="John", is_active=True)
users = await service.get_all(filters)

# 4. Fluent API
users = await repo.query()\\
    .where_eq(User.is_active, True)\\
    .order_by_desc(User.created_at)\\
    .paginate(1, 10)\\
    .find_all()
```

"""

        return section

    def generate_usage_examples(self, modules: Dict[str, ModuleInfo]) -> str:
        """Сгенерировать примеры использования"""
        section = """## 💡 Примеры использования

### Базовая работа с Repository

```python
from dplex import BaseRepository, QueryBuilder
from dplex.filters import FilterSchema

# Создание репозитория
user_repo = BaseRepository(User, session)

# CRUD операции
user = await user_repo.get_by_id(user_id)
users = await user_repo.get_all()
new_user = await user_repo.create(user_entity)
```

### Работа с Service Layer

```python
from dplex import BaseService

class UserService(BaseService[User, uuid.UUID, UserCreateSchema, UserUpdateSchema]):
    async def get_active_users_in_city(self, city: str) -> list[User]:
        filters = UserFilterSchema(city=city, is_active=True)
        return await self.get_all(filters)

# Использование
user_service = UserService(user_repo, session)
users = await user_service.get_active_users_in_city("Moscow")
```

### Типизированные фильтры

```python
from dplex.filters import NumericFilter, StringFilter

@dataclass
class ProductFilterSchema(FilterSchema):
    name: StringFilter | None = None
    price: NumericFilter[float] | None = None
    category_id: IntFilter | None = None

    def apply_filters(self, query: QueryBuilder) -> QueryBuilder:
        if self.name:
            query = query.where_ilike(Product.name, f"%{self.name}%")
        if self.price:
            if self.price.gte:
                query = query.where_gte(Product.price, self.price.gte)
        return query

# Использование
filters = ProductFilterSchema(
    name=StringFilter(ilike="iPhone"),
    price=NumericFilter(gte=100.0, lte=1000.0)
)
```

### Интеграция с FastAPI

```python
from dplex.integrations.fastapi import FilterDepends

@app.get("/users")
async def get_users(
    filters: UserFilterSchema = FilterDepends(),
    user_service: UserService = Depends()
):
    users, total = await user_service.get_paginated(filters)
    return {"items": users, "total": total}
```

"""

        return section

    def generate_development_guidelines(self) -> str:
        """Сгенерировать руководство по разработке"""
        return '''## 👩‍💻 Руководство для разработки

### Принципы разработки

1. **🎯 Типизация превыше всего**
   - Используйте строгую типизацию для всех методов
   - Предпочитайте `list[Type]` вместо `List[Type]`
   - Используйте `| None` вместо `Optional[Type]`

2. **🏗️ Архитектурная чистота**
   - Repository только для доступа к данным
   - Service для бизнес-логики
   - Filter schemas для сложных запросов
   - Миксины для переиспользования функциональности

3. **📝 Документация**
   - Обязательные docstring для публичных методов
   - Примеры использования в docstring
   - Type hints для всех параметров

### Структура нового модуля

```
new_module/
├── __init__.py          # Публичный API
├── base_service.py             # Базовые классы
├── mixins.py           # Миксины
├── exceptions.py       # Исключения модуля
├── types.py            # Типы модуля
└── utils.py            # Утилиты
```

### Паттерн создания Repository

```python
class EntityRepository(BaseRepository[Entity, uuid.UUID]):
    """Repository для работы с сущностью Entity"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Entity, session)

    async def find_by_custom_field(self, value: str) -> list[Entity]:
        """Найти по кастомному полю"""
        return await self.query()\\
            .where_eq(Entity.custom_field, value)\\
            .find_all()
```

### Паттерн создания Service

```python
class EntityService(BaseService[Entity, uuid.UUID, EntityCreateSchema, EntityUpdateSchema]):
    """Сервис для бизнес-логики с Entity"""

    def __init__(self, repo: EntityRepository, session: AsyncSession) -> None:
        super().__init__(repo, session)

    async def business_operation(self, param: str) -> Entity:
        """Бизнес-операция с валидацией и логикой"""
        # Валидация
        await self._validate_business_rules(param)

        # Бизнес-логика
        entity = await self._create_entity_with_logic(param)

        # Аудит/метрики
        await self._log_operation("business_operation", entity.id)

        return entity
```

### Тестирование

```python
@pytest.fixture
async def entity_repo(async_session):
    return EntityRepository(async_session)

@pytest.fixture  
async def entity_service(entity_repo, async_session):
    return EntityService(entity_repo, async_session)

async def test_entity_creation(entity_service):
    # Arrange
    create_data = EntityCreateSchema(name="Test")

    # Act
    entity = await entity_service.create(create_data)

    # Assert
    assert entity.name == "Test"
    assert entity.id is not None
```

### Код стайл

- **Форматтер:** Black (line-length=88)
- **Импорты:** isort с профилем black  
- **Типизация:** mypy в строгом режиме
- **Линтинг:** flake8
- **Документация:** Google style docstrings

---

## 🚀 Команды для разработки

```bash
# Установка зависимостей
poetry install --with dev

# Запуск тестов
poetry run pytest --cov=dplex

# Форматирование кода
poetry run black dplex/
poetry run isort dplex/

# Проверка типов
poetry run mypy dplex/

# Генерация документации  
poetry run mkdocs serve

# Сборка пакета
poetry build

# Публикация
poetry publish
```

'''

    def generate_manual(self) -> str:
        """Сгенерировать полный мануал"""
        print("🔍 Анализируем структуру проекта...")
        modules = self.analyze_project_structure()

        print(f"📦 Найдено модулей: {len(modules)}")

        # Генерируем секции мануала
        sections = [
            self.generate_manual_header(),
            self.generate_architecture_section(modules),
            self.generate_usage_examples(modules),
        ]

        # Добавляем секции для каждого модуля
        print("📝 Генерируем документацию модулей...")
        for module_name in sorted(modules.keys()):
            module_info = modules[module_name]
            sections.append(self.generate_module_section(module_info))

        # Добавляем руководство по разработке
        sections.append(self.generate_development_guidelines())

        return "\n".join(sections)

    def save_manual(self, output_file: str = "dplex_AI_MANUAL.md") -> None:
        """Сохранить мануал в файл"""
        manual_content = self.generate_manual()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(manual_content)

        print(f"✅ Мануал сохранен в файл: {output_file}")
        print(f"📊 Размер файла: {len(manual_content)} символов")


def main():
    """Основная функция"""
    print("🤖 Генератор мануала для ИИ ассистентов")
    print("=" * 50)

    # Определяем корневую директорию проекта
    project_root = (
        input("📁 Путь к проекту (по умолчанию '../../dplex'): ").strip()
        or "../../dplex"
    )

    if not Path(project_root).exists():
        print(f"❌ Директория {project_root} не найдена!")
        return

    # Создаем генератор
    generator = AIManualGenerator(project_root)

    # Генерируем и сохраняем мануал
    try:
        output_file = input(
            "📄 Имя выходного файла (по умолчанию 'dplex_AI_MANUAL.md'): "
        ).strip()
        if not output_file:
            output_file = "dplex_AI_MANUAL.md"

        generator.save_manual(output_file)

        print("\n🎉 Готово!")
        print("📖 Мануал готов к использованию ИИ ассистентами")
        print(f"📁 Файл: {Path(output_file).absolute()}")

    except Exception as e:
        print(f"❌ Ошибка при генерации мануала: {e}")
        raise


if __name__ == "__main__":
    main()
