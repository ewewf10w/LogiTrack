from app.repositories.order_repo import OrderRepository
from app.models.order import Order
from app.models.value_objects import Dimensions, Weight
from app.schemas.order import OrderCreate


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def create_order(self, schema: OrderCreate) -> Order:
        if schema.weight_grams <= 0:
            raise ValueError("Вес груза должен быть положительным числом")

        if any(v <= 0 for v in [schema.width, schema.height, schema.length]):
            raise ValueError("Габариты (ширина, высота, длина) должны быть больше нуля")

        dims = Dimensions(
            width=schema.width, height=schema.height, length=schema.length
        )
        w = Weight(grams=schema.weight_grams)

        new_order = Order(
            title=schema.title,
            description=schema.description,
            dimensions=dims,
            weight=w,
        )

        return await self.repository.create(new_order)

    async def get_all_orders(self):
        return await self.repository.get_all()
