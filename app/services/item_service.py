from app.repositories.item_repo import ItemRepository
from app.models.item import Item
from app.schemas.item import ItemCreate


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    async def create_item(self, schema: ItemCreate) -> Item:
        new_item = Item(name=schema.name, price=schema.price)
        return await self.repository.create(new_item)

    async def get_all_items(self):
        return await self.repository.get_all()
