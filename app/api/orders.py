from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.models.db_helper import db_helper
from app.repositories.order_repo import OrderRepository
from app.repositories.item_repo import ItemRepository
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderRead, OrderPatch

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service(session: AsyncSession = Depends(db_helper.session_getter)):
    return OrderService(
        order_repo=OrderRepository(session), item_repo=ItemRepository(session)
    )


@router.post("/", response_model=OrderRead)
async def create_order(
    order_data: OrderCreate, service: OrderService = Depends(get_order_service)
):
    return await service.create_order(order_data)


@router.get("/", response_model=List[OrderRead])
async def list_orders(service: OrderService = Depends(get_order_service)):
    return await service.get_all_orders()


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
