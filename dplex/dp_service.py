"""Базовый сервис для бизнес-логики с автоматизацией фильтрации, сортировки и CRUD операций"""

from typing import TYPE_CHECKING, Any, Generic
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dplex.internal.filter_applier import FilterApplier
from dplex.internal.types import (
    ModelType,
    KeyType,
    CreateSchemaType,
    UpdateSchemaType,
    ResponseSchemaType,
    FilterSchemaType,
    SortFieldSchemaType,
)

from dplex.dp_repo import DPRepo
from dplex.dp_filters import DPFilters

if TYPE_CHECKING:
    from dplex.internal.query_builder import QueryBuilder
from dplex.internal.sort import Sort, Order


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
    Базовый сервис для бизнес-логики с автоматизацией
    Предоставляет полный набор CRUD операций с автоматической обработкой:
    - Фильтрации через DPFilters
    - Сортировки через Sort объекты
    - Пагинации (limit/offset)
    - Преобразования между моделями и схемами
    Type Parameters:
        ModelType: SQLAlchemy модель
        KeyType: Тип первичного ключа (int, str, UUID)
        CreateSchemaType: Pydantic схема для создания
        UpdateSchemaType: Pydantic схема для обновления
        ResponseSchemaType: Pydantic схема для ответа
        FilterSchemaType: Схема фильтрации (наследник DPFilters)
        SortFieldSchemaType: Enum полей для сортировки
    Attributes:
        repository: Репозиторий для доступа к данным
        session: Асинхронная SQLAlchemy сессия
        response_schema: Класс Pydantic схемы для ответа
        filter_applier: Экземпляр FilterApplier для применения фильтров
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
            session: Асинхронная SQLAlchemy сессия
            response_schema: Класс Pydantic схемы для ответа
        Returns:
            None
        """
        self.repository = repository
        self.session = session
        self.response_schema = response_schema
        self.filter_applier = FilterApplier()

    # ==================== АВТОМАТИЧЕСКИЕ МЕТОДЫ ====================
    def _model_to_schema(self, model: ModelType) -> ResponseSchemaType:
        """
        Автоматическое преобразование SQLAlchemy модели в Pydantic схему
        Использует model_validate из Pydantic для преобразования.
        Args:
            model: Экземпляр SQLAlchemy модели
        Returns:
            Экземпляр Pydantic схемы ответа
        """
        return self.response_schema.model_validate(model)

    def _create_schema_to_model(self, schema: CreateSchemaType) -> ModelType:
        """
        Автоматическое преобразование схемы создания в SQLAlchemy модель
        Работает через model_dump() и **kwargs в конструктор модели.
        Args:
            schema: Схема создания с данными
        Returns:
            Новый экземпляр SQLAlchemy модели
        """
        return self.repository.model(**schema.model_dump(exclude_unset=True))

    def _apply_filter_to_query(
        self, query_builder: "QueryBuilder[ModelType]", filter_data: FilterSchemaType
    ) -> "QueryBuilder[ModelType]":
        """
        Автоматическое применение фильтров к query builder
        Работает с DPFilters - автоматически применяет все активные фильтры.
        Args:
            query_builder: QueryBuilder для добавления фильтров
            filter_data: Схема фильтра (DPFilters)
        Returns:
            QueryBuilder с примененными фильтрами
        """
        # Если filter_data это наследник DPFilters
        if isinstance(filter_data, DPFilters):
            # Автоматически применяем все активные фильтры (обычные)
            query_builder = self.filter_applier.apply_filters_from_schema(
                query_builder, self.repository.model, filter_data
            )
            # Применяем кастомные фильтры (поля, которых нет в модели)
            query_builder = self.apply_custom_filters(query_builder, filter_data)
        return query_builder

    def apply_custom_filters(
        self, query_builder: "QueryBuilder[ModelType]", filter_data: FilterSchemaType
    ) -> "QueryBuilder[ModelType]":
        """
        Применить кастомные фильтры к query builder

        Кастомные фильтры - это поля в схеме фильтрации, которых нет в модели.
        Этот метод можно переопределить в наследниках для обработки специфичных фильтров.

        Args:
            query_builder: QueryBuilder для добавления фильтров
            filter_data: Схема фильтра (DPFilters)

        Returns:
            QueryBuilder с примененными кастомными фильтрами

        Examples:
            >>> class UserService(DPService[...]):
            ...     def apply_custom_filters(self, query_builder, filter_data):
            ...         # Получаем кастомные фильтры
            ...         custom_filters = filter_data.get_custom_filters(self.repository.model)
            ...
            ...         # Обрабатываем фильтр 'query' для поиска по нескольким полям
            ...         if 'query' in custom_filters:
            ...             query_filter = custom_filters['query']
            ...             if hasattr(query_filter, 'icontains') and query_filter.icontains:
            ...                 search_term = query_filter.icontains
            ...                 from sqlalchemy import or_
            ...                 query_builder = query_builder.where(
            ...                     or_(
            ...                         User.name.ilike(f'%{search_term}%'),
            ...                         User.email.ilike(f'%{search_term}%')
            ...                     )
            ...                 )
            ...         return query_builder
        """
        if isinstance(filter_data, DPFilters):
            # Получаем кастомные фильтры (поля, которых нет в модели)
            custom_filters = filter_data.get_custom_filters(self.repository.model)
            # По умолчанию ничего не делаем - можно переопределить в наследниках
            # Это позволяет пользователям добавлять свою логику обработки кастомных фильтров
            pass
        return query_builder

    def _get_custom_filters(self, filter_data: FilterSchemaType) -> dict[str, Any]:
        """
        Получить кастомные фильтры из схемы фильтрации

        Helper метод для получения кастомных фильтров (полей, которых нет в модели).

        Args:
            filter_data: Схема фильтра (DPFilters)

        Returns:
            Словарь {field_name: filter_instance} с кастомными фильтрами

        Examples:
            >>> custom_filters = self._get_custom_filters(filter_data)
            >>> if 'query' in custom_filters:
            ...     # Обработать фильтр 'query'
        """
        if isinstance(filter_data, DPFilters):
            return filter_data.get_custom_filters(self.repository.model)
        return {}

    def _apply_string_filter_operation(
        self,
        query_builder: "QueryBuilder[ModelType]",
        filter_instance: Any,
        operation: str,
        columns: list[Any],
        case_sensitive: bool = False,
    ) -> "QueryBuilder[ModelType]":
        """
        Применить операцию StringFilter к нескольким колонкам через OR

        Helper метод для упрощения обработки StringFilter операций
        при поиске по нескольким полям одновременно.

        Args:
            query_builder: QueryBuilder для добавления фильтров
            filter_instance: Экземпляр StringFilter
            operation: Название операции ('icontains', 'contains', 'eq', 'starts_with', 'ends_with')
            columns: Список колонок модели для поиска
            case_sensitive: Учитывать регистр (True) или нет (False)

        Returns:
            QueryBuilder с примененным условием поиска

        Examples:
            >>> from sqlalchemy import or_
            >>> columns = [User.name, User.email, User.bio]
            >>> query_builder = self._apply_string_filter_operation(
            ...     query_builder, query_filter, 'icontains', columns, case_sensitive=False
            ... )
        """
        from sqlalchemy import or_

        if not hasattr(filter_instance, operation):
            return query_builder

        search_term = getattr(filter_instance, operation, None)
        if not search_term:
            return query_builder

        conditions = []
        for column in columns:
            if operation == "icontains":
                conditions.append(column.ilike(f"%{search_term}%"))
            elif operation == "contains":
                conditions.append(column.like(f"%{search_term}%"))
            elif operation == "eq":
                conditions.append(column == search_term)
            elif operation == "starts_with":
                if case_sensitive:
                    conditions.append(column.like(f"{search_term}%"))
                else:
                    conditions.append(column.ilike(f"{search_term}%"))
            elif operation == "ends_with":
                if case_sensitive:
                    conditions.append(column.like(f"%{search_term}"))
                else:
                    conditions.append(column.ilike(f"%{search_term}"))

        if conditions:
            query_builder = query_builder.where(or_(*conditions))

        return query_builder

    @staticmethod
    def _sort_field_to_column_name(sort_field: SortFieldSchemaType) -> str:
        """
        Автоматическое преобразование enum поля сортировки в имя колонки
        Использует .value из enum (для StrEnum это будет имя колонки).
        Args:
            sort_field: Enum поле для сортировки
        Returns:
            Имя колонки в виде строки
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
        return []

    @staticmethod
    def _make_update_dict(update_data: BaseModel) -> dict[str, Any]:
        """
        Сформировать словарь для частичного обновления записи
        Метод анализирует модель и возвращает только те поля, которые были
        реально переданы пользователем при создании экземпляра (на основе model_fields_set).
        Логика:
        - Поля, не переданные пользователем, не попадают в результат
        - Поля, переданные со значением None, будут установлены в NULL в БД
        - Поля, переданные с любым другим значением, обновляются этим значением
        Args:
            update_data: Экземпляр Pydantic модели обновления
        Returns:
            Словарь с парами {имя_поля: значение} для передачи в репозиторий
        """
        return update_data.model_dump(exclude_unset=True)

    def _apply_base_filters(
        self, query_builder: Any, filter_data: FilterSchemaType
    ) -> Any:
        """
        Применить базовые фильтры: фильтрация, сортировка, limit, offset
        Автоматически извлекает всё из DPFilters.
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
        if not entity_ids:
            raise ValueError("DPService.get_by_ids: Список ID не может быть пустым")

        models = await self.repository.find_by_ids(entity_ids)
        return self._models_to_schemas(models)

    async def get_all(self, filter_data: FilterSchemaType) -> list[ResponseSchemaType]:
        """
        Получить все сущности с фильтрацией и сортировкой
        Автоматически применяет все фильтры, сортировку, limit и offset из DPFilters.
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
        if not create_data_list:
            raise ValueError(
                "DPService.create_bulk: Список для создания не может быть пустым"
            )

        models = [self._create_schema_to_model(data) for data in create_data_list]
        created_models = await self.repository.create_bulk(models)
        await self.session.flush()
        return self._models_to_schemas(created_models)

    async def update(
        self,
        filter_data: FilterSchemaType,
        update_data: UpdateSchemaType,
    ) -> None:
        """
        Массовое обновление по фильтрам
        Применяет только фильтры из filter_data (без сортировки, limit, offset).
        Обновляет только поля, явно переданные в update_data.
        Args:
            filter_data: Схема фильтра для выборки записей
            update_data: Схема обновления с новыми данными
        Returns:
            None
        """
        update_dict = self._make_update_dict(update_data)
        if not update_dict:
            raise ValueError(
                "DPService.update: Данные для обновления не могут быть пустыми"
            )

        qb = self.repository.query()
        qb = self._apply_filter_to_query(qb, filter_data)
        await self.repository.update_by_query_builder(qb, update_dict)
        await self.session.flush()

    async def update_by_id(
        self,
        entity_id: KeyType,
        update_data: UpdateSchemaType,
    ) -> None:
        """
        Обновить сущность по ID
        Args:
            entity_id: Первичный ключ
            update_data: Схема обновления с новыми данными
        Returns:
            None
        """
        update_dict = self._make_update_dict(update_data)
        if not update_dict:
            raise ValueError(
                "DPService.update_by_id: Данные для обновления не могут быть пустыми"
            )

        await self.repository.update_by_id(entity_id, update_dict)
        await self.session.flush()

    async def update_by_ids(
        self,
        entity_ids: list[KeyType],
        update_data: UpdateSchemaType,
    ) -> None:
        """
        Обновить несколько сущностей по списку ID
        Args:
            entity_ids: Список первичных ключей
            update_data: Схема обновления (одинаковая для всех)
        Returns:
            None
        """
        if not entity_ids:
            raise ValueError("DPService.update_by_ids: Список ID не может быть пустым")

        update_dict = self._make_update_dict(update_data)
        if not update_dict:
            raise ValueError(
                "DPService.update_by_ids: Данные для обновления не могут быть пустыми"
            )

        await self.repository.update_by_ids(entity_ids, update_dict)
        await self.session.flush()

    async def delete(self, filter_data: FilterSchemaType) -> None:
        """
        Массовое удаление записей по фильтрам
        Создает QueryBuilder, применяет фильтры и выполняет массовое DELETE.
        Args:
            filter_data: Схема с параметрами фильтрации (DPFilters)
        Returns:
            None
        """
        qb = self.repository.query()
        qb = self._apply_filter_to_query(qb, filter_data)
        await self.repository.delete_by_query_builder(qb)

    async def delete_by_id(self, entity_id: KeyType) -> None:
        """
        Удалить сущность по ID
        Args:
            entity_id: Первичный ключ
        Returns:
            None
        """
        await self.repository.delete_by_id(entity_id)

    async def delete_by_ids(self, entity_ids: list[KeyType]) -> None:
        """
        Удалить несколько сущностей по списку ID
        Args:
            entity_ids: Список первичных ключей
        Returns:
            None
        """
        if not entity_ids:
            raise ValueError("DPService.delete_by_ids: Список ID не может быть пустым")

        await self.repository.delete_by_ids(entity_ids)

    async def paginate(
        self, page: int, per_page: int, filter_data: FilterSchemaType
    ) -> tuple[list[ResponseSchemaType], int]:
        """
        Пагинация с фильтрацией и сортировкой
        Автоматически использует DPFilters для фильтрации и сортировки.
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
            raise ValueError("DPService.paginate: Номер страницы должен быть >= 1")
        if per_page < 1:
            raise ValueError(
                "DPService.paginate: Количество на странице должно быть >= 1"
            )

        total_count = await self.count(filter_data)

        if isinstance(filter_data, BaseModel):
            paginated_filter = filter_data.model_copy()
        else:
            paginated_filter = filter_data

        if isinstance(paginated_filter, DPFilters):
            paginated_filter.limit = per_page
            paginated_filter.offset = (page - 1) * per_page

        items = await self.get_all(paginated_filter)
        return items, total_count
