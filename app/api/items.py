from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.models.db_helper import db_helper
from app.repositories.item_repo import ItemRepository
from app.services.item_service import ItemService
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate
from app.models.user import User
from app.authentication.fastapi_users import current_active_user

router = APIRouter(prefix="/items", tags=["Items"])


def get_item_service(session: AsyncSession = Depends(db_helper.session_getter)):
    return ItemService(ItemRepository(session))


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    schema: ItemCreate,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(current_active_user),
):
    return await service.create_item(schema, current_user)


@router.get("/", response_model=List[ItemRead])
async def list_items(service: ItemService = Depends(get_item_service)):
    return await service.get_all_items()


@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    schema: ItemUpdate,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(current_active_user),
):
    return await service.update_item(item_id, schema, current_user)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(current_active_user),
):
    await service.delete_item(item_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
