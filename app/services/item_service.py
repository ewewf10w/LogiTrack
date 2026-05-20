from fastapi import HTTPException, status
from app.repositories.item_repo import ItemRepository
from app.models.item import Item
from app.models.user import User, UserRole
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    def _verify_admin_or_manager(self, user: User):
        if user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для управления товарами.",
            )

    async def create_item(self, schema: ItemCreate, current_user: User) -> Item:
        self._verify_admin_or_manager(current_user)
        new_item = Item(**schema.model_dump())
        return await self.repository.create(new_item)

    async def get_all_items(self):
        return await self.repository.get_all()

    async def update_item(
        self, item_id: int, schema: ItemUpdate, current_user: User
    ) -> Item:
        self._verify_admin_or_manager(current_user)
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Товар не найден")

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        return await self.repository.update(item)

    async def delete_item(self, item_id: int, current_user: User) -> None:
        self._verify_admin_or_manager(current_user)
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Товар не найден")
        await self.repository.delete(item)
