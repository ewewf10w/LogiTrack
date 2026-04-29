from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.repositories.order_repo import OrderRepository
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderRead, OrderPatch

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service(db: AsyncSession = Depends(get_db)):
    return OrderService(OrderRepository(db))


@router.post("/", response_model=OrderRead)
async def create_order(
    order_data: OrderCreate, service: OrderService = Depends(get_order_service)
):
    try:
        return await service.create_order(order_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[OrderRead])
async def list_orders(service: OrderService = Depends(get_order_service)):
    return await service.get_all_orders()


@router.patch("/{order_id}", response_model=OrderRead)
async def patch_order(
    order_id: int,
    order_data: OrderPatch,
    service: OrderService = Depends(get_order_service),
):
    try:
        return await service.patch_order(order_id, order_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int, service: OrderService = Depends(get_order_service)
):
    try:
        await service.delete_order(order_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
