from typing import Any, Generic, TypeVar, Literal
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from dplex import BaseRepository
from dplex.types import ModelType, KeyType

# Типы для схем
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
FilterSchemaType = TypeVar("FilterSchemaType", bound="BaseFilter")
SortFieldSchemaType = TypeVar("SortFieldSchemaType", bound=str)


class SortDirection(str, Enum):
    """Направления сортировки"""

    ASC = "asc"
    DESC = "desc"


class StringFilter(BaseModel):
    """Фильтр для строковых полей"""

    eq: str | None = None
    ne: str | None = None
    like: str | None = None
    ilike: str | None = None
    contains: str | None = None
    icontains: str | None = None
    starts_with: str | None = None
    ends_with: str | None = None
    in_: list[str] | None = Field(None, alias="in")
    not_in: list[str] | None = None
    is_null: bool | None = None
    is_not_null: bool | None = None


class NumberFilter(BaseModel):
    """Фильтр для числовых полей"""

    eq: float | int | None = None
    ne: float | int | None = None
    gt: float | int | None = None
    gte: float | int | None = None
    lt: float | int | None = None
    lte: float | int | None = None
    between: tuple[float | int, float | int] | None = None
    in_: list[float | int] | None = Field(None, alias="in")
    not_in: list[float | int] | None = None
    is_null: bool | None = None
    is_not_null: bool | None = None


class DateTimeFilter(BaseModel):
    """Фильтр для datetime полей"""

    eq: datetime | None = None
    ne: datetime | None = None
    gt: datetime | None = None
    gte: datetime | None = None
    lt: datetime | None = None
    lte: datetime | None = None
    between: tuple[datetime, datetime] | None = None
    from_: datetime | None = Field(None, alias="from")
    to: datetime | None = None
    in_: list[datetime] | None = Field(None, alias="in")
    not_in: list[datetime] | None = None
    is_null: bool | None = None
    is_not_null: bool | None = None

    def model_post_init(self, __context: Any) -> None:
        """Обработка after model validation"""
        if self.from_ is not None and self.gte is None:
            self.gte = self.from_
        if self.to is not None and self.lte is None:
            self.lte = self.to


class BooleanFilter(BaseModel):
    """Фильтр для boolean полей"""

    eq: bool | None = None
    ne: bool | None = None
    is_null: bool | None = None
    is_not_null: bool | None = None


class FilterableFields(BaseModel):
    """Базовая схема для описания фильтруемых полей модели"""

    pass


class BaseFilter(BaseModel):
    """Базовый фильтр с общими полями"""

    limit: int | None = None
    offset: int | None = None
    sort_direction: SortDirection = SortDirection.ASC


class BaseFilterApplier:
    """Класс для применения базовых фильтров к query builder"""

    @staticmethod
    def apply_string_filter(
        query_builder: Any, column: Any, filter_data: StringFilter
    ) -> Any:
        """Применить строковый фильтр"""
        if filter_data.eq is not None:
            query_builder = query_builder.where_eq(column, filter_data.eq)

        if filter_data.ne is not None:
            query_builder = query_builder.where_ne(column, filter_data.ne)

        if filter_data.like is not None:
            query_builder = query_builder.where_like(column, filter_data.like)

        if filter_data.ilike is not None:
            query_builder = query_builder.where_ilike(column, filter_data.ilike)

        if filter_data.contains is not None:
            pattern = f"%{filter_data.contains}%"
            query_builder = query_builder.where_like(column, pattern)

        if filter_data.icontains is not None:
            pattern = f"%{filter_data.icontains}%"
            query_builder = query_builder.where_ilike(column, pattern)

        if filter_data.starts_with is not None:
            pattern = f"{filter_data.starts_with}%"
            query_builder = query_builder.where_like(column, pattern)

        if filter_data.ends_with is not None:
            pattern = f"%{filter_data.ends_with}"
            query_builder = query_builder.where_like(column, pattern)

        if filter_data.in_ is not None:
            query_builder = query_builder.where_in(column, filter_data.in_)

        if filter_data.not_in is not None:
            query_builder = query_builder.where_not_in(column, filter_data.not_in)

        if filter_data.is_null is True:
            query_builder = query_builder.where_is_null(column)

        if filter_data.is_not_null is True:
            query_builder = query_builder.where_is_not_null(column)

        return query_builder

    @staticmethod
    def apply_number_filter(
        query_builder: Any, column: Any, filter_data: NumberFilter
    ) -> Any:
        """Применить числовой фильтр"""
        if filter_data.eq is not None:
            query_builder = query_builder.where_eq(column, filter_data.eq)

        if filter_data.ne is not None:
            query_builder = query_builder.where_ne(column, filter_data.ne)

        if filter_data.gt is not None:
            query_builder = query_builder.where_gt(column, filter_data.gt)

        if filter_data.gte is not None:
            query_builder = query_builder.where_gte(column, filter_data.gte)

        if filter_data.lt is not None:
            query_builder = query_builder.where_lt(column, filter_data.lt)

        if filter_data.lte is not None:
            query_builder = query_builder.where_lte(column, filter_data.lte)

        if filter_data.between is not None:
            start, end = filter_data.between
            query_builder = query_builder.where_between(column, start, end)

        if filter_data.in_ is not None:
            query_builder = query_builder.where_in(column, filter_data.in_)

        if filter_data.not_in is not None:
            query_builder = query_builder.where_not_in(column, filter_data.not_in)

        if filter_data.is_null is True:
            query_builder = query_builder.where_is_null(column)

        if filter_data.is_not_null is True:
            query_builder = query_builder.where_is_not_null(column)

        return query_builder

    @staticmethod
    def apply_datetime_filter(
        query_builder: Any, column: Any, filter_data: DateTimeFilter
    ) -> Any:
        """Применить datetime фильтр"""
        if filter_data.eq is not None:
            query_builder = query_builder.where_eq(column, filter_data.eq)

        if filter_data.ne is not None:
            query_builder = query_builder.where_ne(column, filter_data.ne)

        if filter_data.gt is not None:
            query_builder = query_builder.where_gt(column, filter_data.gt)

        if filter_data.gte is not None:
            query_builder = query_builder.where_gte(column, filter_data.gte)

        if filter_data.lt is not None:
            query_builder = query_builder.where_lt(column, filter_data.lt)

        if filter_data.lte is not None:
            query_builder = query_builder.where_lte(column, filter_data.lte)

        if filter_data.between is not None:
            start, end = filter_data.between
            query_builder = query_builder.where_between(column, start, end)

        if filter_data.in_ is not None:
            query_builder = query_builder.where_in(column, filter_data.in_)

        if filter_data.not_in is not None:
            query_builder = query_builder.where_not_in(column, filter_data.not_in)

        if filter_data.is_null is True:
            query_builder = query_builder.where_is_null(column)

        if filter_data.is_not_null is True:
            query_builder = query_builder.where_is_not_null(column)

        return query_builder

    @staticmethod
    def apply_boolean_filter(
        query_builder: Any, column: Any, filter_data: BooleanFilter
    ) -> Any:
        """Применить boolean фильтр"""
        if filter_data.eq is not None:
            query_builder = query_builder.where_eq(column, filter_data.eq)

        if filter_data.ne is not None:
            query_builder = query_builder.where_ne(column, filter_data.ne)

        if filter_data.is_null is True:
            query_builder = query_builder.where_is_null(column)

        if filter_data.is_not_null is True:
            query_builder = query_builder.where_is_not_null(column)

        return query_builder

    def apply_filters_from_schema(
        self, query_builder: Any, model: type, filterable_fields: FilterableFields
    ) -> Any:
        """Применить все фильтры из схемы FilterableFields автоматически"""
        for field_name, field_value in filterable_fields.model_dump(
            exclude_none=True
        ).items():
            if field_value is None:
                continue

            if not hasattr(model, field_name):
                continue

            column = getattr(model, field_name)

            if isinstance(field_value, dict):
                if any(
                    k in field_value
                    for k in [
                        "contains",
                        "icontains",
                        "starts_with",
                        "ends_with",
                        "like",
                        "ilike",
                    ]
                ):
                    filter_obj = StringFilter(**field_value)
                    query_builder = self.apply_string_filter(
                        query_builder, column, filter_obj
                    )
                elif any(
                    k in field_value for k in ["gt", "gte", "lt", "lte", "between"]
                ):
                    first_value = next(
                        (v for v in field_value.values() if v is not None), None
                    )
                    if isinstance(first_value, datetime):
                        filter_obj = DateTimeFilter(**field_value)
                        query_builder = self.apply_datetime_filter(
                            query_builder, column, filter_obj
                        )
                    else:
                        filter_obj = NumberFilter(**field_value)
                        query_builder = self.apply_number_filter(
                            query_builder, column, filter_obj
                        )
                elif "eq" in field_value:
                    eq_value = field_value["eq"]
                    if isinstance(eq_value, bool):
                        filter_obj = BooleanFilter(**field_value)
                        query_builder = self.apply_boolean_filter(
                            query_builder, column, filter_obj
                        )
                    elif isinstance(eq_value, str):
                        filter_obj = StringFilter(**field_value)
                        query_builder = self.apply_string_filter(
                            query_builder, column, filter_obj
                        )
                    elif isinstance(eq_value, (int, float)):
                        filter_obj = NumberFilter(**field_value)
                        query_builder = self.apply_number_filter(
                            query_builder, column, filter_obj
                        )
                    elif isinstance(eq_value, datetime):
                        filter_obj = DateTimeFilter(**field_value)
                        query_builder = self.apply_datetime_filter(
                            query_builder, column, filter_obj
                        )

        return query_builder


class BaseService(
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
    """Базовый сервис с типизированными схемами и фильтрами"""

    def __init__(
        self,
        repository: BaseRepository[ModelType, KeyType],
        session: AsyncSession,
        response_schema: type[ResponseSchemaType],
    ) -> None:
        self.repository = repository
        self.session = session
        self.response_schema = response_schema
        self.filter_applier = BaseFilterApplier()

    @abstractmethod
    def _model_to_schema(self, model: ModelType) -> ResponseSchemaType:
        """Преобразовать модель в схему ответа"""
        pass

    @abstractmethod
    def _create_schema_to_model(self, schema: CreateSchemaType) -> ModelType:
        """Преобразовать схему создания в модель"""
        pass

    @abstractmethod
    def _apply_filter_to_query(
        self, query_builder: Any, filter_data: FilterSchemaType
    ) -> Any:
        """Применить фильтр к query builder"""
        pass

    @abstractmethod
    def _parse_sort_field(self, sort_field: SortFieldSchemaType) -> list[str]:
        """Распарсить поле сортировки в список имен колонок.

        Этот метод должен быть реализован в наследниках для определения
        того, как конкретный тип сортировки преобразуется в колонки модели.

        Args:
            sort_field: Значение поля сортировки (например, Literal или enum)

        Returns:
            Список имен колонок модели для сортировки

        Example:
            # Для простого случая (один к одному):
            def _parse_sort_field(self, sort_field: UserSortField) -> list[str]:
                return [sort_field]

            # Для составной сортировки:
            def _parse_sort_field(self, sort_field: UserSortField) -> list[str]:
                if sort_field == "full_name":
                    return ["first_name", "last_name"]
                return [sort_field]
        """
        pass

    def _get_model_column(self, field_name: str) -> Any:
        """Получить колонку модели по имени поля"""
        if not hasattr(self.repository.model, field_name):
            raise ValueError(
                f"Model {self.repository.model.__name__} has no field '{field_name}'"
            )
        return getattr(self.repository.model, field_name)

    def _get_sort_fields_from_filter(
        self, filter_data: FilterSchemaType
    ) -> list[tuple[str, SortDirection]]:
        """Получить список полей сортировки из фильтра"""
        if not hasattr(filter_data, "sort_field") or filter_data.sort_field is None:
            return []

        sort_field = filter_data.sort_field
        sort_direction = getattr(filter_data, "sort_direction", SortDirection.ASC)

        # Используем абстрактный метод для парсинга
        column_names = self._parse_sort_field(sort_field)

        # Применяем одно направление ко всем колонкам
        return [(col_name, sort_direction) for col_name in column_names]

    def _apply_base_filters(
        self, query_builder: Any, filter_data: FilterSchemaType
    ) -> Any:
        """Применить базовые фильтры (limit, offset, sort)"""
        # Применяем пользовательские фильтры
        query_builder = self._apply_filter_to_query(query_builder, filter_data)

        # Применяем сортировку
        sort_fields = self._get_sort_fields_from_filter(filter_data)
        for field_name, direction in sort_fields:
            column = self._get_model_column(field_name)
            desc = direction == SortDirection.DESC
            query_builder = query_builder.order_by(column, desc=desc)

        if hasattr(filter_data, "limit") and filter_data.limit is not None:
            query_builder = query_builder.limit(filter_data.limit)

        if hasattr(filter_data, "offset") and filter_data.offset is not None:
            query_builder = query_builder.offset(filter_data.offset)

        return query_builder

    def _models_to_schemas(self, models: list[ModelType]) -> list[ResponseSchemaType]:
        """Преобразовать список моделей в схемы"""
        return [self._model_to_schema(model) for model in models]

    async def get_by_id(self, entity_id: KeyType) -> ResponseSchemaType | None:
        """Получить сущность по ID"""
        model = await self.repository.find_by_id(entity_id)
        if model is None:
            return None
        return self._model_to_schema(model)

    async def get_by_ids(self, entity_ids: list[KeyType]) -> list[ResponseSchemaType]:
        """Получить сущности по списку ID"""
        models = await self.repository.find_by_ids(entity_ids)
        return self._models_to_schemas(models)

    async def get_all(self, filter_data: FilterSchemaType) -> list[ResponseSchemaType]:
        """Получить все сущности с фильтрацией"""
        query_builder = self.repository.query()
        query_builder = self._apply_base_filters(query_builder, filter_data)
        models = await query_builder.find_all()
        return self._models_to_schemas(models)

    async def get_first(
        self, filter_data: FilterSchemaType
    ) -> ResponseSchemaType | None:
        """Получить первую сущность с фильтрацией"""
        query_builder = self.repository.query()
        query_builder = self._apply_filter_to_query(query_builder, filter_data)
        model = await query_builder.find_one()
        if model is None:
            return None
        return self._model_to_schema(model)

    async def count(self, filter_data: FilterSchemaType) -> int:
        """Подсчитать количество сущностей с фильтрацией"""
        query_builder = self.repository.query()
        query_builder = self._apply_filter_to_query(query_builder, filter_data)
        return await query_builder.count()

    async def exists(self, filter_data: FilterSchemaType) -> bool:
        """Проверить существование сущностей с фильтрацией"""
        count = await self.count(filter_data)
        return count > 0

    async def exists_by_id(self, entity_id: KeyType) -> bool:
        """Проверить существование сущности по ID"""
        return await self.repository.exists_by_id(entity_id)

    async def create(self, create_data: CreateSchemaType) -> ResponseSchemaType:
        """Создать новую сущность"""
        model = self._create_schema_to_model(create_data)
        created_model = await self.repository.create(model)
        return self._model_to_schema(created_model)

    async def create_bulk(
        self, create_data_list: list[CreateSchemaType]
    ) -> list[ResponseSchemaType]:
        """Создать несколько сущностей"""
        models = [self._create_schema_to_model(data) for data in create_data_list]
        created_models = await self.repository.create_bulk(models)
        return self._models_to_schemas(created_models)

    async def update_by_id(
        self,
        entity_id: KeyType,
        update_data: UpdateSchemaType,
        include_none: bool = False,
    ) -> ResponseSchemaType | None:
        """Обновить сущность по ID"""
        existing_model = await self.repository.find_by_id(entity_id)
        if existing_model is None:
            return None

        if include_none:
            update_dict = update_data.model_dump(exclude_unset=True)
        else:
            update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

        await self.repository.update_by_id(entity_id, update_dict)

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
        """Обновить несколько сущностей по ID"""
        if include_none:
            update_dict = update_data.model_dump(exclude_unset=True)
        else:
            update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)

        await self.repository.update_by_ids(entity_ids, update_dict)

        updated_models = await self.repository.find_by_ids(entity_ids)
        return self._models_to_schemas(updated_models)

    async def update_by_id_with_fields(
        self,
        entity_id: KeyType,
        update_data: UpdateSchemaType,
        fields_to_update: list[str],
    ) -> ResponseSchemaType | None:
        """Обновить сущность по ID с явным указанием полей для обновления"""
        existing_model = await self.repository.find_by_id(entity_id)
        if existing_model is None:
            return None

        full_dump = update_data.model_dump()

        update_dict = {
            field: full_dump[field] for field in fields_to_update if field in full_dump
        }

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
        """Обновить несколько сущностей по ID с явным указанием полей для обновления"""
        full_dump = update_data.model_dump()

        update_dict = {
            field: full_dump[field] for field in fields_to_update if field in full_dump
        }

        await self.repository.update_by_ids(entity_ids, update_dict)

        updated_models = await self.repository.find_by_ids(entity_ids)
        return self._models_to_schemas(updated_models)

    async def delete_by_id(self, entity_id: KeyType) -> bool:
        """Удалить сущность по ID"""
        exists = await self.repository.exists_by_id(entity_id)
        if not exists:
            return False
        await self.repository.delete_by_id(entity_id)
        return True

    async def delete_by_ids(self, entity_ids: list[KeyType]) -> int:
        """Удалить несколько сущностей по ID. Возвращает количество удаленных"""
        existing_models = await self.repository.find_by_ids(entity_ids)
        existing_count = len(existing_models)

        if existing_count > 0:
            await self.repository.delete_by_ids(entity_ids)

        return existing_count

    async def paginate(
        self, page: int, per_page: int, filter_data: FilterSchemaType
    ) -> tuple[list[ResponseSchemaType], int]:
        """Пагинация с фильтрацией. Возвращает (данные, общее_количество)"""
        if page < 1:
            raise ValueError("Page must be >= 1")
        if per_page < 1:
            raise ValueError("Per page must be >= 1")

        total_count = await self.count(filter_data)

        paginated_filter = filter_data.model_copy()
        if hasattr(paginated_filter, "limit"):
            paginated_filter.limit = per_page
        if hasattr(paginated_filter, "offset"):
            paginated_filter.offset = (page - 1) * per_page

        items = await self.get_all(paginated_filter)

        return items, total_count
