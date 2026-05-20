from sqlalchemy import select, delete
from app.models.item import Item
from app.repositories.base import BaseRepository
from typing import List, Optional


class ItemRepository(BaseRepository):
    async def get_all(self) -> List[Item]:
        query = select(Item)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_ids(self, item_ids: List[int]) -> List[Item]:
        query = select(Item).where(Item.id.in_(item_ids))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, item: Item) -> Item:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: int) -> Optional[Item]:
        query = select(Item).where(Item.id == item_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, item: Item) -> Item:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item: Item) -> None:
        await self.session.delete(item)
        await self.session.commit()
