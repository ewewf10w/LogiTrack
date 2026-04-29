from sqlalchemy import select
from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_all(self):
        query = select(Order)
        result = await self.session.execute(query)
        return result.scalars().all()
