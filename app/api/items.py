from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.models.db_helper import db_helper
from app.repositories.item_repo import ItemRepository
from app.services.item_service import ItemService
from app.schemas.item import ItemCreate, ItemRead

router = APIRouter(prefix="/items", tags=["Items"])


def get_item_service(session: AsyncSession = Depends(db_helper.session_getter)):
    return ItemService(ItemRepository(session))


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: ItemCreate,
    service: ItemService = Depends(get_item_service),
):
    return await service.create_item(item_data)


@router.get("/", response_model=List[ItemRead])
async def list_items(service: ItemService = Depends(get_item_service)):
    return await service.get_all_items()
