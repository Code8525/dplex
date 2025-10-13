"""Базовый сервис для бизнес-логики"""

from typing import Any, Generic
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

from dplex.repositories.repository import DPRepo
from dplex.services.filter_applier import FilterApplier
from dplex.services.sort import Sort, SortDirection, NullsPlacement
from dplex.types import (
    ModelType,
    KeyType,
    CreateSchemaType,
    UpdateSchemaType,
    ResponseSchemaType,
    FilterSchemaType,
    SortFieldSchemaType,
)


class DPService(
    Generic[
        ModelType,
        KeyType,
        CreateSchemaType,
        UpdateSchemaType,
        ResponseSchemaType,
        FilterSchemaType,
        SortFieldSchemaType,
    ],
    ABC,
):
    """
    Базовый сервис с типизированными схемами и фильтрами

    Предоставляет полный CRUD функционал с поддержкой:
    - Типизированных схем (создание, обновление, ответ)
    - Фильтрации и сортировки
    - Пагинации
    - Массовых операций

    Type Parameters:
        ModelType: SQLAlchemy модель
        KeyType: Тип первичного ключа (int, str, UUID)
        CreateSchemaType: Pydantic схема для создания
        UpdateSchemaType: Pydantic схема для обновления
        ResponseSchemaType: Pydantic схема для ответа
        FilterSchemaType: Схема фильтрации
        SortFieldSchemaType: Enum полей для сортировки
    """

    def __init__(
        self,
        repository: DPRepo[ModelType, KeyType],
        session: AsyncSession,
        response_schema: type[ResponseSchemaType],
    ) -> None:
        """
        Инициализация сервиса

        Args:
            repository: Репозиторий для доступа к данным
            session: Async SQLAlchemy сессия
            response_schema: Класс Pydantic схемы для ответа
        """
        self.repository = repository
        self.session = session
        self.response_schema = response_schema
        self.filter_applier = FilterApplier()

    def _model_to_schema(self, model: ModelType) -> ResponseSchemaType:
        """
        Преобразовать SQLAlchemy модель в Pydantic схему ответа

        Дефолтная реализация использует model_validate.
        Переопределите для кастомной логики преобразования.
        """
        return self.response_schema.model_validate(model)

    @abstractmethod
    def _create_schema_to_model(self, schema: CreateSchemaType) -> ModelType:
        """
        Преобразовать схему создания в SQLAlchemy модель

        ОБЯЗАТЕЛЬНО переопределить в наследнике.

        Args:
            schema: Pydantic схема создания

        Returns:
            Новая SQLAlchemy модель (не сохраненная в БД)

        Example:
            def _create_schema_to_model(self, schema: UserCreate) -> User:
                return User(
                    username=schema.username,
                    email=schema.email,
                    password_hash=hash_password(schema.password)
                )
        """
        pass

    @abstractmethod
    def _apply_filter_to_query(
        self, query_builder: Any, filter_data: FilterSchemaType
    ) -> Any:
        """
        Применить фильтры из схемы к query builder

        ОБЯЗАТЕЛЬНО переопределить в наследнике.

        Args:
            query_builder: QueryBuilder для добавления фильтров
            filter_data: Схема с данными фильтрации

        Returns:
            QueryBuilder с примененными фильтрами

        Example:
            def _apply_filter_to_query(self, qb, filter_data: UserFilter):
                if filter_data.username:
                    qb = self.filter_applier.apply_string_filter(
                        qb, User.username, filter_data.username
                    )
                if filter_data.is_active:
                    qb = self.filter_applier.apply_boolean_filter(
                        qb, User.is_active, filter_data.is_active
                    )
                return qb
        """
        pass

    @abstractmethod
    def _sort_field_to_column_name(self, sort_field: SortFieldSchemaType) -> str:
        """
        Преобразовать enum поля сортировки в имя колонки модели

        ОБЯЗАТЕЛЬНО переопределить в наследнике.

        Args:
            sort_field: Enum значение поля для сортировки

        Returns:
            Имя колонки SQLAlchemy модели

        Example:
            def _sort_field_to_column_name(self, sort_field: UserSortField) -> str:
                mapping = {
                    UserSortField.USERNAME: "username",
                    UserSortField.CREATED_AT: "created_at",
                    UserSortField.EMAIL: "email",
                }
                return mapping[sort_field]
        """
        pass

    def _get_model_column(self, field_name: str) -> Any:
        """
        Получить колонку SQLAlchemy модели по имени поля

        Args:
            field_name: Имя атрибута модели

        Returns:
            InstrumentedAttribute колонки

        Raises:
            ValueError: Если поле не существует в модели
        """
        if not hasattr(self.repository.model, field_name):
            raise ValueError(
                f"Модель {self.repository.model.__name__} не имеет поля '{field_name}'"
            )
        return getattr(self.repository.model, field_name)

    def _normalize_sort_list(
        self, sort: list[Sort[SortFieldSchemaType]] | Sort[SortFieldSchemaType] | None
    ) -> list[Sort[SortFieldSchemaType]]:
        """
        Нормализовать сортировку в список

        Args:
            sort: Один элемент Sort, список Sort или None

        Returns:
            Список элементов сортировки (может быть пустым)
        """
        if sort is None:
            return []
        if isinstance(sort, list):
            return sort
        return [sort]

    def _apply_sort_to_query(
        self,
        query_builder: Any,
        sort_list: list[Sort[SortFieldSchemaType]],
    ) -> Any:
        """
        Применить сортировку к query builder

        Args:
            query_builder: QueryBuilder для добавления сортировки
            sort_list: Список элементов сортировки

        Returns:
            QueryBuilder с примененной сортировкой
        """
        for sort_item in sort_list:
            column_name = self._sort_field_to_column_name(sort_item.field)
            column = self._get_model_column(column_name)

            desc_order = sort_item.direction == SortDirection.DESC

            # Используем order_by_with_nulls для поддержки nulls placement
            query_builder = query_builder.order_by_with_nulls(
                column, desc_order=desc_order, nulls_placement=sort_item.nulls
            )

        return query_builder

    def _get_sort_from_filter(
        self, filter_data: FilterSchemaType
    ) -> list[Sort[SortFieldSchemaType]]:
        """
        Извлечь сортировку из схемы фильтра

        Args:
            filter_data: Схема фильтра

        Returns:
            Список элементов Sort
        """
        # Проверяем наличие поля sort в фильтре
        if not hasattr(filter_data, "sort"):
            return []

        sort_value = getattr(filter_data, "sort", None)
        return self._normalize_sort_list(sort_value)

    def _make_update_dict(
        self,
        update_data: UpdateSchemaType,
        include_none: bool = False,
        fields_to_update: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Создать словарь для обновления из Pydantic схемы

        Args:
            update_data: Pydantic схема с данными обновления
            include_none: Включать ли поля со значением None
            fields_to_update: Явный список полей для обновления (если указан, include_none игнорируется)

        Returns:
            Словарь {field_name: value} для передачи в repository.update
        """
        if fields_to_update is not None:
            # Режим явного указания полей (включая None значения)
            full_dump = update_data.model_dump()
            return {
                field: full_dump[field]
                for field in fields_to_update
                if field in full_dump
            }

        # Автоматический режим
        if include_none:
            # Все установленные поля, включая None
            return update_data.model_dump(exclude_unset=True)
        else:
            # Только установленные не-None поля
            return update_data.model_dump(exclude_unset=True, exclude_none=True)

    def _apply_base_filters(
        self, query_builder: Any, filter_data: FilterSchemaType
    ) -> Any:
        """
        Применить базовые фильтры: фильтрация, сортировка, limit, offset

        Args:
            query_builder: QueryBuilder
            filter_data: Схема фильтра

        Returns:
            QueryBuilder с примененными фильтрами
        """
        # 1. Применяем кастомные фильтры
        query_builder = self._apply_filter_to_query(query_builder, filter_data)

        # 2. Применяем сортировку из Sort объектов
        sort_list = self._get_sort_from_filter(filter_data)
        if sort_list:
            query_builder = self._apply_sort_to_query(query_builder, sort_list)

        # 3. Применяем limit
        if hasattr(filter_data, "limit") and filter_data.limit is not None:
            query_builder = query_builder.limit(filter_data.limit)

        # 4. Применяем offset
        if hasattr(filter_data, "offset") and filter_data.offset is not None:
            query_builder = query_builder.offset(filter_data.offset)

        return query_builder

    def _models_to_schemas(self, models: list[ModelType]) -> list[ResponseSchemaType]:
        """
        Преобразовать список моделей в список схем

        Args:
            models: Список SQLAlchemy моделей

        Returns:
            Список Pydantic схем ответа
        """
        return [self._model_to_schema(model) for model in models]

    # ==================== CRUD ОПЕРАЦИИ ====================

    async def get_by_id(self, entity_id: KeyType) -> ResponseSchemaType | None:
        """
        Получить сущность по ID

        Args:
            entity_id: Первичный ключ

        Returns:
            Схема ответа или None если не найдено
        """
        model = await self.repository.find_by_id(entity_id)
        if model is None:
            return None
        return self._model_to_schema(model)

    async def get_by_ids(self, entity_ids: list[KeyType]) -> list[ResponseSchemaType]:
        """
        Получить несколько сущностей по списку ID

        Args:
            entity_ids: Список первичных ключей

        Returns:
            Список схем ответа (только для найденных сущностей)
        """
        models = await self.repository.find_by_ids(entity_ids)
        return self._models_to_schemas(models)

    async def get_all(self, filter_data: FilterSchemaType) -> list[ResponseSchemaType]:
        """
        Получить все сущности с фильтрацией и сортировкой

        Args:
            filter_data: Схема фильтра с параметрами поиска

        Returns:
            Список схем ответа
        """
        query_builder = self.repository.query()
        query_builder = self._apply_base_filters(query_builder, filter_data)
        models = await query_builder.find_all()
        return self._models_to_schemas(models)

    async def get_first(
        self, filter_data: FilterSchemaType
    ) -> ResponseSchemaType | None:
        """
        Получить первую сущность с фильтрацией

        Args:
            filter_data: Схема фильтра

        Returns:
            Первая найденная схема или None
        """
        query_builder = self.repository.query()
        query_builder = self._apply_filter_to_query(query_builder, filter_data)
        model = await query_builder.find_one()
        if model is None:
            return None
        return self._model_to_schema(model)

    async def count(self, filter_data: FilterSchemaType) -> int:
        """
        Подсчитать количество сущностей с фильтрацией

        Args:
            filter_data: Схема фильтра

        Returns:
            Количество записей
        """
        query_builder = self.repository.query()
        query_builder = self._apply_filter_to_query(query_builder, filter_data)
        return await query_builder.count()

    async def exists(self, filter_data: FilterSchemaType) -> bool:
        """
        Проверить существование хотя бы одной сущности с фильтрацией

        Args:
            filter_data: Схема фильтра

        Returns:
            True если хотя бы одна запись найдена
        """
        count = await self.count(filter_data)
        return count > 0

    async def exists_by_id(self, entity_id: KeyType) -> bool:
        """
        Проверить существование сущности по ID

        Args:
            entity_id: Первичный ключ

        Returns:
            True если сущность существует
        """
        return await self.repository.exists_by_id(entity_id)

    async def create(self, create_data: CreateSchemaType) -> ResponseSchemaType:
        """
        Создать новую сущность

        Args:
            create_data: Схема создания с данными

        Returns:
            Схема ответа с созданной сущностью
        """
        model = self._create_schema_to_model(create_data)
        created_model = await self.repository.create(model)
        return self._model_to_schema(created_model)

    async def create_bulk(
        self, create_data_list: list[CreateSchemaType]
    ) -> list[ResponseSchemaType]:
        """
        Создать несколько сущностей одновременно (bulk insert)

        Args:
            create_data_list: Список схем создания

        Returns:
            Список схем ответа с созданными сущностями
        """
        models = [self._create_schema_to_model(data) for data in create_data_list]
        created_models = await self.repository.create_bulk(models)
        return self._models_to_schemas(created_models)

    async def update_by_id(
        self,
        entity_id: KeyType,
        update_data: UpdateSchemaType,
        include_none: bool = False,
    ) -> ResponseSchemaType | None:
        """
        Обновить сущность по ID

        Args:
            entity_id: Первичный ключ
            update_data: Схема обновления с новыми данными
            include_none: Если True, поля со значением None также будут обновлены

        Returns:
            Обновленная схема ответа или None если сущность не найдена
        """
        # Проверяем существование
        existing_model = await self.repository.find_by_id(entity_id)
        if existing_model is None:
            return None

        # Обновляем
        update_dict = self._make_update_dict(update_data, include_none=include_none)
        await self.repository.update_by_id(entity_id, update_dict)

        # Получаем обновленную версию
        updated_model = await self.repository.find_by_id(entity_id)
        if updated_model is None:
            return None

        return self._model_to_schema(updated_model)

    async def update_by_ids(
        self,
        entity_ids: list[KeyType],
        update_data: UpdateSchemaType,
        include_none: bool = False,
    ) -> list[ResponseSchemaType]:
        """
        Обновить несколько сущностей по списку ID

        Args:
            entity_ids: Список первичных ключей
            update_data: Схема обновления (одинаковая для всех)
            include_none: Если True, поля со значением None также будут обновлены

        Returns:
            Список обновленных схем ответа
        """
        update_dict = self._make_update_dict(update_data, include_none=include_none)
        await self.repository.update_by_ids(entity_ids, update_dict)

        updated_models = await self.repository.find_by_ids(entity_ids)
        return self._models_to_schemas(updated_models)

    async def update_by_id_with_fields(
        self,
        entity_id: KeyType,
        update_data: UpdateSchemaType,
        fields_to_update: list[str],
    ) -> ResponseSchemaType | None:
        """
        Обновить сущность по ID с явным указанием полей

        Полезно когда нужно обновить конкретные поля, включая установку NULL.

        Args:
            entity_id: Первичный ключ
            update_data: Схема обновления
            fields_to_update: Явный список имен полей для обновления

        Returns:
            Обновленная схема ответа или None если сущность не найдена

        Example:
            await service.update_by_id_with_fields(
                user_id,
                UserUpdate(email=None, name="John"),
                fields_to_update=["email", "name"]  # email будет установлен в NULL
            )
        """
        existing_model = await self.repository.find_by_id(entity_id)
        if existing_model is None:
            return None

        update_dict = self._make_update_dict(
            update_data, fields_to_update=fields_to_update
        )
        await self.repository.update_by_id(entity_id, update_dict)

        updated_model = await self.repository.find_by_id(entity_id)
        if updated_model is None:
            return None

        return self._model_to_schema(updated_model)

    async def update_by_ids_with_fields(
        self,
        entity_ids: list[KeyType],
        update_data: UpdateSchemaType,
        fields_to_update: list[str],
    ) -> list[ResponseSchemaType]:
        """
        Обновить несколько сущностей с явным указанием полей

        Args:
            entity_ids: Список первичных ключей
            update_data: Схема обновления
            fields_to_update: Явный список имен полей для обновления

        Returns:
            Список обновленных схем ответа
        """
        update_dict = self._make_update_dict(
            update_data, fields_to_update=fields_to_update
        )
        await self.repository.update_by_ids(entity_ids, update_dict)

        updated_models = await self.repository.find_by_ids(entity_ids)
        return self._models_to_schemas(updated_models)

    async def delete_by_id(self, entity_id: KeyType) -> bool:
        """
        Удалить сущность по ID

        Args:
            entity_id: Первичный ключ

        Returns:
            True если сущность была удалена, False если не существовала
        """
        exists = await self.repository.exists_by_id(entity_id)
        if not exists:
            return False

        await self.repository.delete_by_id(entity_id)
        return True

    async def delete_by_ids(self, entity_ids: list[KeyType]) -> int:
        """
        Удалить несколько сущностей по списку ID

        Args:
            entity_ids: Список первичных ключей

        Returns:
            Количество фактически удаленных записей
        """
        # Проверяем какие сущности существуют
        existing_models = await self.repository.find_by_ids(entity_ids)
        existing_count = len(existing_models)

        if existing_count > 0:
            await self.repository.delete_by_ids(entity_ids)

        return existing_count

    async def paginate(
        self, page: int, per_page: int, filter_data: FilterSchemaType
    ) -> tuple[list[ResponseSchemaType], int]:
        """
        Пагинация с фильтрацией и сортировкой

        Args:
            page: Номер страницы (начиная с 1)
            per_page: Количество элементов на странице
            filter_data: Схема фильтра

        Returns:
            Кортеж (список_данных, общее_количество)

        Raises:
            ValueError: Если page < 1 или per_page < 1
        """
        if page < 1:
            raise ValueError("Номер страницы должен быть >= 1")
        if per_page < 1:
            raise ValueError("Количество на странице должно быть >= 1")

        # Подсчитываем общее количество
        total_count = await self.count(filter_data)

        # Создаем копию фильтра с пагинацией
        paginated_filter = filter_data.model_copy()

        # Устанавливаем limit и offset
        if hasattr(paginated_filter, "limit"):
            paginated_filter.limit = per_page
        if hasattr(paginated_filter, "offset"):
            paginated_filter.offset = (page - 1) * per_page

        # Получаем данные для страницы
        items = await self.get_all(paginated_filter)

        return items, total_count
