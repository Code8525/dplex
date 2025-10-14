"""Базовый сервис для бизнес-логики с ПОЛНОЙ автоматизацией"""

from typing import Any, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from dplex.repositories.dp_repo import DPRepo
from dplex.services.filter_applier import FilterApplier
from dplex.services.dp_filters import DPFilters
from dplex.services.sort import Sort, Order
from dplex.types import (
    ModelType,
    KeyType,
    CreateSchemaType,
    UpdateSchemaType,
    ResponseSchemaType,
    FilterSchemaType,
    SortFieldSchemaType,
    NullMarker,
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
    ]
):
    """
    Базовый сервис с ПОЛНОЙ автоматизацией

    ВСЁ работает автоматически:
    ✓ Создание моделей из схем (автоматически по полям)
    ✓ Применение фильтров (автоматически через DPFilters)
    ✓ Сортировка (автоматически по именам enum)
    ✓ Пагинация (автоматически через limit/offset в DPFilters)
    ✓ CRUD операции
    ✓ Установка NULL через маркер NULL

    НЕ НУЖНО переопределять методы!

    Type Parameters:
        ModelType: SQLAlchemy модель
        KeyType: Тип первичного ключа (int, str, UUID)
        CreateSchemaType: Pydantic схема для создания
        UpdateSchemaType: Pydantic схема для обновления
        ResponseSchemaType: Pydantic схема для ответа
        FilterSchemaType: Схема фильтрации (наследник DPFilters)
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

    # ==================== АВТОМАТИЧЕСКИЕ МЕТОДЫ ====================

    def _model_to_schema(self, model: ModelType) -> ResponseSchemaType:
        """
        АВТОМАТИЧЕСКОЕ преобразование SQLAlchemy модели в Pydantic схему

        Использует model_validate из Pydantic.
        """
        return self.response_schema.model_validate(model)

    def _create_schema_to_model(self, schema: CreateSchemaType) -> ModelType:
        """
        АВТОМАТИЧЕСКОЕ преобразование схемы создания в SQLAlchemy модель

        Работает через model_dump() и **kwargs в конструктор модели.
        """
        if isinstance(schema, BaseModel):
            data = schema.model_dump(exclude_unset=True)
        else:
            data = schema.__dict__

        return self.repository.model(**data)

    def _apply_filter_to_query(
        self, query_builder: Any, filter_data: FilterSchemaType
    ) -> Any:
        """
        АВТОМАТИЧЕСКОЕ применение фильтров к query builder

        Работает с DPFilters - автоматически применяет все активные фильтры.
        """
        # Если filter_data это наследник DPFilters
        if isinstance(filter_data, DPFilters):
            # Автоматически применяем все активные фильтры
            query_builder = self.filter_applier.apply_filters_from_schema(
                query_builder, self.repository.model, filter_data
            )

        return query_builder

    @staticmethod
    def _sort_field_to_column_name(sort_field: SortFieldSchemaType) -> str:
        """
        АВТОМАТИЧЕСКОЕ преобразование enum поля сортировки в имя колонки

        Использует .value из enum (для StrEnum это будет имя колонки).
        """
        return str(sort_field.value)

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

    @staticmethod
    def _normalize_sort_list(
        sort: list[Sort[SortFieldSchemaType]] | Sort[SortFieldSchemaType] | None,
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
            column_name = self._sort_field_to_column_name(sort_item.by)
            column = self._get_model_column(column_name)

            desc_order = sort_item.order == Order.DESC

            # Используем order_by_with_nulls для поддержки nulls placement
            query_builder = query_builder.order_by_with_nulls(
                column, desc_order=desc_order, nulls_placement=sort_item.nulls
            )

        return query_builder

    def _get_sort_from_filter(
        self, filter_data: FilterSchemaType
    ) -> list[Sort[SortFieldSchemaType]]:
        """
        Извлечь сортировку из схемы фильтра (DPFilters)

        Args:
            filter_data: Схема фильтра

        Returns:
            Список элементов Sort
        """
        # DPFilters гарантирует наличие поля sort
        if isinstance(filter_data, DPFilters):
            return self._normalize_sort_list(filter_data.sort)

        # Fallback для старых схем без DPFilters
        if hasattr(filter_data, "sort"):
            return self._normalize_sort_list(filter_data.sort)

        return []

    @staticmethod
    def _make_update_dict(
        update_data: UpdateSchemaType,
        fields_to_update: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Создать словарь для обновления из Pydantic схемы

        ПОДДЕРЖКА МАРКЕРА NULL:
        - Поле не указано (exclude_unset) -> НЕ обновляем
        - Поле = NULL (маркер) -> обновляем в None (NULL в БД)
        - Поле = обычное значение -> обновляем значением

        Args:
            update_data: Pydantic схема с данными обновления
            fields_to_update: Явный список полей для обновления (если None - все установленные)

        Returns:
            Словарь {field_name: value} для передачи в repository.update

        Examples:
            >>> from dplex import NULL

            >>> # Обновить только name
            >>> data = UserUpdate(name="John")
            >>> _make_update_dict(data)
            {'name': 'John'}

            >>> # Установить email в NULL
            >>> data = UserUpdate(email=NULL)
            >>> _make_update_dict(data)
            {'email': None}

            >>> # Смешанное обновление
            >>> data = UserUpdate(name="John", email=NULL, age=30)
            >>> _make_update_dict(data)
            {'name': 'John', 'email': None, 'age': 30}

            >>> # С явным списком полей
            >>> data = UserUpdate(name="John", email=NULL, age=30)
            >>> _make_update_dict(data, fields_to_update=["email"])
            {'email': None}
        """
        if isinstance(update_data, BaseModel):
            if fields_to_update is not None:
                # Режим явного указания полей
                full_dump = update_data.model_dump()
                result = {}
                for field in fields_to_update:
                    if field in full_dump:
                        value = full_dump[field]
                        # Преобразуем Marker.NULL в None для БД
                        if isinstance(value, NullMarker):
                            result[field] = None
                        else:
                            result[field] = value
                return result

            # Автоматический режим - только установленные поля
            dump = update_data.model_dump(exclude_unset=True)
            result = {}

            for field_name, field_value in dump.items():
                # Обрабатываем маркер NULL
                if isinstance(field_value, NullMarker):
                    result[field_name] = None  # NULL маркер -> None в БД
                else:
                    # Обычное значение (включая None)
                    result[field_name] = field_value

            return result
        else:
            # Fallback для не-Pydantic объектов
            return update_data.__dict__

    def _apply_base_filters(
        self, query_builder: Any, filter_data: FilterSchemaType
    ) -> Any:
        """
        Применить базовые фильтры: фильтрация, сортировка, limit, offset

        АВТОМАТИЧЕСКИ извлекает всё из DPFilters.

        Args:
            query_builder: QueryBuilder
            filter_data: Схема фильтра (DPFilters)

        Returns:
            QueryBuilder с примененными фильтрами
        """
        # 1. Применяем кастомные фильтры (автоматически)
        query_builder = self._apply_filter_to_query(query_builder, filter_data)

        # 2. Применяем сортировку из Sort объектов (автоматически из DPFilters)
        sort_list = self._get_sort_from_filter(filter_data)
        if sort_list:
            query_builder = self._apply_sort_to_query(query_builder, sort_list)

        # 3. Применяем limit (автоматически из DPFilters)
        if isinstance(filter_data, DPFilters) and filter_data.limit is not None:
            query_builder = query_builder.limit(filter_data.limit)

        # 4. Применяем offset (автоматически из DPFilters)
        if isinstance(filter_data, DPFilters) and filter_data.offset is not None:
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

        АВТОМАТИЧЕСКИ применяет все фильтры, сортировку, limit и offset из DPFilters.

        Args:
            filter_data: Схема фильтра с параметрами поиска (DPFilters)

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
        await self.session.flush()
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
        await self.session.flush()
        return self._models_to_schemas(created_models)

    async def update_by_id(
        self,
        entity_id: KeyType,
        update_data: UpdateSchemaType,
    ) -> ResponseSchemaType | None:
        """
        Обновить сущность по ID

        ПОДДЕРЖКА NULL:
        Используйте маркер NULL для явной установки NULL в БД.

        Логика обновления:
        - Поле не указано -> не обновляется (остаётся прежнее значение)
        - Поле = значение -> обновляется значением
        - Поле = NULL -> устанавливается в NULL (удаляется значение)

        Args:
            entity_id: Первичный ключ
            update_data: Схема обновления с новыми данными

        Returns:
            Обновленная схема ответа или None если сущность не найдена

        Examples:
            >>> from dplex import NULL

            >>> # Обновить только name
            >>> user = await service.update_by_id(
            ...     user_id,
            ...     UserUpdate(name="John Doe")
            ... )

            >>> # Обновить name и установить email в NULL
            >>> user = await service.update_by_id(
            ...     user_id,
            ...     UserUpdate(name="John", email=NULL)
            ... )

            >>> # Установить несколько полей в NULL
            >>> user = await service.update_by_id(
            ...     user_id,
            ...     UserUpdate(email=NULL, phone=NULL, bio=NULL)
            ... )
        """
        # Проверяем существование
        existing_model = await self.repository.find_by_id(entity_id)
        if existing_model is None:
            return None

        # Обновляем
        update_dict = self._make_update_dict(update_data)
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
    ) -> list[ResponseSchemaType]:
        """
        Обновить несколько сущностей по списку ID

        ПОДДЕРЖКА NULL:
        Маркер NULL работает для массового обновления.

        Args:
            entity_ids: Список первичных ключей
            update_data: Схема обновления (одинаковая для всех)

        Returns:
            Список обновленных схем ответа

        Examples:
            >>> from dplex import NULL

            >>> # Деактивировать нескольких пользователей
            >>> users = await service.update_by_ids(
            ...     [1, 2, 3],
            ...     UserUpdate(is_active=False)
            ... )

            >>> # Очистить email у нескольких пользователей
            >>> users = await service.update_by_ids(
            ...     [4, 5, 6],
            ...     UserUpdate(email=NULL)
            ... )
        """
        update_dict = self._make_update_dict(update_data)
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

        ПОДДЕРЖКА NULL:
        Маркер NULL работает с явным списком полей.

        Args:
            entity_id: Первичный ключ
            update_data: Схема обновления
            fields_to_update: Явный список имен полей для обновления

        Returns:
            Обновленная схема ответа или None если сущность не найдена

        Examples:
            >>> from dplex import NULL

            >>> # Обновить только email (установить в NULL)
            >>> user = await service.update_by_id_with_fields(
            ...     user_id,
            ...     UserUpdate(name="Ignored", email=NULL),
            ...     fields_to_update=["email"]
            ... )
            # name не будет обновлён, email будет NULL

            >>> # Обновить несколько полей выборочно
            >>> user = await service.update_by_id_with_fields(
            ...     user_id,
            ...     UserUpdate(name="John", email=NULL, age=30, bio="Dev"),
            ...     fields_to_update=["name", "email"]
            ... )
            # Обновятся только name и email, age и bio игнорируются
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

        АВТОМАТИЧЕСКИ использует DPFilters для фильтрации и сортировки.

        Args:
            page: Номер страницы (начиная с 1)
            per_page: Количество элементов на странице
            filter_data: Схема фильтра (DPFilters)

        Returns:
            Кортеж (список_данных, общее_количество)

        Raises:
            ValueError: Если page < 1 или per_page < 1
        """
        if page < 1:
            raise ValueError("Номер страницы должен быть >= 1")
        if per_page < 1:
            raise ValueError("Количество на странице должно быть >= 1")

        # Подсчитываем общее количество (без пагинации)
        total_count = await self.count(filter_data)

        # Создаем копию фильтра с пагинацией
        if isinstance(filter_data, BaseModel):
            paginated_filter = filter_data.model_copy()
        else:
            # Fallback для не-Pydantic объектов
            paginated_filter = filter_data

        # Устанавливаем limit и offset в DPFilters
        if isinstance(paginated_filter, DPFilters):
            paginated_filter.limit = per_page
            paginated_filter.offset = (page - 1) * per_page

        # Получаем данные для страницы
        items = await self.get_all(paginated_filter)

        return items, total_count
