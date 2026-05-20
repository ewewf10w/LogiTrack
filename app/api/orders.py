from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.models.db_helper import db_helper
from app.repositories.order_repo import OrderRepository
from app.repositories.item_repo import ItemRepository
from app.services.order_service import OrderService
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderRead, OrderPatch
from app.models.user import User
from app.authentication.fastapi_users import current_active_user

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service(session: AsyncSession = Depends(db_helper.session_getter)):
    return OrderService(
        order_repo=OrderRepository(session), item_repo=ItemRepository(session)
    )


@router.post("/", response_model=OrderRead)
async def create_order(
    order_data: OrderCreate,
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(current_active_user),
):
    return await service.create_order(order_data, user_id=current_user.id)


@router.get("/", response_model=List[OrderRead])
async def list_orders(
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(current_active_user),
):
    return await service.get_orders_for_user(current_user)


@router.patch("/{order_id}", response_model=OrderRead)
async def patch_order(
    order_id: int,
    order_data: OrderPatch,
    service: OrderService = Depends(get_order_service),
):
    return await service.patch_order(order_id, order_data)


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: int, service: OrderService = Depends(get_order_service)
):
    await service.delete_order(order_id)
    return Response(status_code=204)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    current_user: User = Depends(current_active_user),
    service: OrderService = Depends(get_order_service),
):
    return await service.change_order_status(
        order_id=order_id, new_status=new_status, current_user=current_user
    )


@router.get("/available", response_model=List[OrderRead])
async def list_available_orders(
    service: OrderService = Depends(get_order_service),
    current_user: User = Depends(current_active_user),
):
    return await service.get_available_orders(current_user)
