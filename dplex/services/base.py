"""Base service implementation"""

from typing import Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.base_repository import BaseRepository
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

    @staticmethod
    def _prepare_create_data(create_data: CreateSchemaType) -> dict[str, Any]:
        """Prepare data for creation"""
        if hasattr(create_data, 'model_dump'):
            return create_data.model_dump(exclude_none=True)
        elif hasattr(create_data, '__dict__'):
            return create_data.__dict__
        elif isinstance(create_data, dict):
            return create_data
        else:
            raise ValueError(f"Unsupported create_data type: {type(create_data)}")
