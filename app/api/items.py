from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.repositories.item_repo import ItemRepository
from app.services.item_service import ItemService
from app.schemas.item import ItemCreate, ItemRead

router = APIRouter(prefix="/items", tags=["Items"])


def get_item_service(db: AsyncSession = Depends(get_db)):
    return ItemService(ItemRepository(db))


@router.post("/", response_model=ItemRead)
async def create_item(
    item_data: ItemCreate, service: ItemService = Depends(get_item_service)
):
    return await service.create_item(item_data)


@router.get("/", response_model=List[ItemRead])
async def list_items(service: ItemService = Depends(get_item_service)):
    return await service.get_all_items()
