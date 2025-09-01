from sqlalchemy.ext.asyncio import AsyncSession


# Repository classes for data access
class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model_class, id: int):
        """Get entity by ID."""
        return await self.session.get(model_class, id)

    async def create(self, entity):
        """Create new entity."""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity):
        """Update existing entity."""
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity):
        """Delete entity."""
        await self.session.delete(entity)
        await self.session.commit()
