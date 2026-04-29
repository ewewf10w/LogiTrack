from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.repositories.order_repo import OrderRepository
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderRead

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
