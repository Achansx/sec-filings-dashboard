"""Base CRUD operations for database models."""
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict, Union
from pydantic import BaseModel
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations.

    Provides common database operations for models.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD object with model.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            session: Database session
            id: Record ID

        Returns:
            Model instance or None
        """
        query = select(self.model).where(self.model.id == id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any,
    ) -> Optional[ModelType]:
        """
        Get a single record by field value.

        Args:
            session: Database session
            field_name: Field name
            field_value: Field value to match

        Returns:
            Model instance or None
        """
        field = getattr(self.model, field_name)
        query = select(self.model).where(field == field_value)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field name to order by (prefix with '-' for descending)

        Returns:
            List of model instances
        """
        query = select(self.model).offset(skip).limit(limit)

        # Add ordering if specified
        if order_by:
            if order_by.startswith("-"):
                field = getattr(self.model, order_by[1:])
                query = query.order_by(field.desc())
            else:
                field = getattr(self.model, order_by)
                query = query.order_by(field)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_count(self, session: AsyncSession) -> int:
        """
        Get total count of records.

        Args:
            session: Database session

        Returns:
            Total count
        """
        query = select(func.count()).select_from(self.model)
        result = await session.execute(query)
        return result.scalar_one()

    async def create(
        self,
        session: AsyncSession,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Create a new record.

        Args:
            session: Database session
            obj_in: Pydantic schema or dict with data

        Returns:
            Created model instance
        """
        # Convert Pydantic model to dict if necessary
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.model_dump(exclude_unset=True)

        # Create model instance
        db_obj = self.model(**obj_data)
        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            session: Database session
            db_obj: Existing model instance
            obj_in: Pydantic schema or dict with update data

        Returns:
            Updated model instance
        """
        # Convert Pydantic model to dict if necessary
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Update fields
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        session.add(db_obj)
        await session.flush()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Delete a record by ID.

        Args:
            session: Database session
            id: Record ID

        Returns:
            Deleted model instance or None
        """
        db_obj = await self.get(session, id)
        if db_obj:
            await session.delete(db_obj)
            await session.flush()
        return db_obj

    async def exists(self, session: AsyncSession, id: Any) -> bool:
        """
        Check if a record exists by ID.

        Args:
            session: Database session
            id: Record ID

        Returns:
            True if record exists, False otherwise
        """
        query = select(func.count()).where(self.model.id == id).select_from(self.model)
        result = await session.execute(query)
        count = result.scalar_one()
        return count > 0

    async def exists_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any,
    ) -> bool:
        """
        Check if a record exists by field value.

        Args:
            session: Database session
            field_name: Field name
            field_value: Field value to match

        Returns:
            True if record exists, False otherwise
        """
        field = getattr(self.model, field_name)
        query = select(func.count()).where(field == field_value).select_from(self.model)
        result = await session.execute(query)
        count = result.scalar_one()
        return count > 0
