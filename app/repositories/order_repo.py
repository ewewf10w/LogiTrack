from typing import List, Optional, Tuple
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import joinedload, selectinload
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.repositories.base import BaseRepository
from app.schemas.order import OrderFilterParams


class OrderRepository(BaseRepository):
    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()

        query = (
            select(Order)
            .where(Order.id == order.id)
            .options(joinedload(Order.order_items).joinedload(OrderItem.item))
        )

        result = await self.session.execute(query)
        return result.unique().scalar_one()

    async def get_all(self):
        query = select(Order).options(
            selectinload(Order.order_items).joinedload(OrderItem.item)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, order_id: int) -> Order | None:
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.order_items).joinedload(OrderItem.item))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, order: Order) -> None:
        await self.session.delete(order)
        await self.session.commit()

    async def get_all_by_client(self, client_id: int):
        query = (
            select(Order)
            .where(Order.user_id == client_id)
            .options(selectinload(Order.order_items).joinedload(OrderItem.item))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_by_courier(self, courier_id: int):
        query = (
            select(Order)
            .where(Order.courier_id == courier_id)
            .options(selectinload(Order.order_items).joinedload(OrderItem.item))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()

        query = (
            select(Order)
            .where(Order.id == order.id)
            .options(joinedload(Order.order_items).joinedload(OrderItem.item))
        )
        result = await self.session.execute(query)
        return result.unique().scalar_one()

    async def get_available_orders(self):
        query = (
            select(Order)
            .where(Order.status == OrderStatus.NEW)
            .options(selectinload(Order.order_items).joinedload(OrderItem.item))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    def _build_filtered_query(self, base_query, params: OrderFilterParams):
        if params.status is not None:
            base_query = base_query.where(Order.status == params.status)

        if params.sort_by.startswith("-"):
            field_name = params.sort_by[1:]
            base_query = base_query.order_by(desc(getattr(Order, field_name, Order.id)))
        else:
            base_query = base_query.order_by(
                asc(getattr(Order, params.sort_by, Order.id))
            )

        return base_query

    async def get_orders_paginated(
        self,
        params: OrderFilterParams,
        client_id: Optional[int] = None,
        courier_id: Optional[int] = None,
    ) -> Tuple[List[Order], int]:
        base_query = select(Order)

        if client_id is not None:
            base_query = base_query.where(Order.user_id == client_id)
        elif courier_id is not None:
            base_query = base_query.where(Order.courier_id == courier_id)

        base_query = self._build_filtered_query(base_query, params)

        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        items_query = (
            base_query.limit(params.limit)
            .offset(params.offset)
            .options(selectinload(Order.order_items).joinedload(OrderItem.item))
        )
        items_result = await self.session.execute(items_query)
        items = items_result.scalars().all()

        return items, total
