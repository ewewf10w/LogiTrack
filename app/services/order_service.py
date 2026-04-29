from app.repositories.order_repo import OrderRepository
from app.models.order import Order
from app.models.value_objects import Dimensions, Weight
from app.schemas.order import OrderCreate, OrderPatch


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

    async def patch_order(self, order_id: int, schema: OrderPatch) -> Order:
        order = await self.repository.get_by_id(order_id)
        if not order:
            raise ValueError("Заказ не найден")

        if order.version != schema.version:
            raise ValueError("Данные устарели. Кто-то другой уже изменил этот заказ.")

        if schema.title is not None:
            order.title = schema.title
        if schema.description is not None:
            order.description = schema.description

        if any(v is not None for v in [schema.width, schema.height, schema.length]):
            order.dimensions = Dimensions(
                width=(
                    schema.width if schema.width is not None else order.dimensions.width
                ),
                height=(
                    schema.height
                    if schema.height is not None
                    else order.dimensions.height
                ),
                length=(
                    schema.length
                    if schema.length is not None
                    else order.dimensions.length
                ),
            )

        if schema.weight_grams is not None:
            order.weight = Weight(grams=schema.weight_grams)

        order.version += 1
        return await self.repository.create(order)

    async def delete_order(self, order_id: int) -> None:
        order = await self.repository.get_by_id(order_id)
        if not order:
            raise ValueError("Заказ не найден.")

        await self.repository.delete(order)
