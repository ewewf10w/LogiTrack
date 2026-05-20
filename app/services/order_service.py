from fastapi import HTTPException

from app.models.user import User, UserRole
from app.repositories.item_repo import ItemRepository
from app.repositories.order_repo import OrderRepository
from app.models.order import Order, OrderStatus
from app.models.value_objects import Dimensions, Weight
from app.schemas import order
from app.schemas.order import OrderCreate, OrderPatch, OrderStatus


class OrderService:
    def __init__(self, order_repo: OrderRepository, item_repo: ItemRepository):
        self.order_repo = order_repo
        self.item_repo = item_repo

    async def create_order(self, schema: OrderCreate, user_id: int) -> Order:
        dims = Dimensions(
            width=schema.width, height=schema.height, length=schema.length
        )
        w = Weight(grams=schema.weight_grams)

        items = await self.item_repo.get_by_ids(schema.item_ids)
        if len(items) != len(schema.item_ids):
            raise ValueError("Некоторые товары не найдены")

        if schema.weight_grams <= 0:
            raise ValueError("Вес груза должен быть положительным числом")

        if any(v <= 0 for v in [schema.width, schema.height, schema.length]):
            raise ValueError("Габариты (ширина, высота, длина) должны быть больше нуля")

        if w.kg > 500:
            raise ValueError("Мы не перевозим грузы тяжелее 500 кг")

        if dims.volume_m3 > 10:
            raise ValueError("Объем груза слишком велик для наших машин")

        dims = Dimensions(
            width=schema.width, height=schema.height, length=schema.length
        )
        w = Weight(grams=schema.weight_grams)

        new_order = Order(
            title=schema.title,
            description=schema.description,
            dimensions=dims,
            weight=w,
            user_id=user_id,
            items=items,
        )

        return await self.order_repo.create(new_order)

    async def get_all_orders(self):
        return await self.order_repo.get_all()

    async def get_orders_for_user(self, user: User):

        if user.role in (UserRole.ADMIN, UserRole.MANAGER):
            return await self.order_repo.get_all()

        if user.role == UserRole.COURIER:
            return await self.order_repo.get_all_by_courier(user.id)

        return await self.order_repo.get_all_by_client(user.id)

    async def patch_order(self, order_id: int, schema: OrderPatch) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Заказ не найден")

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя редактировать заказ в статусе {order.status.value}",
            )

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
        return await self.order_repo.create(order)

    async def delete_order(self, order_id: int) -> None:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Заказ не найден.")

        await self.order_repo.delete(order)

    async def change_order_status(
        self, order_id: int, new_status: OrderStatus, current_user
    ) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        old_status = order.status

        if old_status == new_status:
            return order

        ALLOWED_TRANSITIONS = {
            OrderStatus.NEW: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
            OrderStatus.ACCEPTED: [OrderStatus.IN_DELIVERY, OrderStatus.CANCELLED],
            OrderStatus.IN_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }

        if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Невозможный перевод статуса из {old_status.value} в {new_status.value}",
            )

        if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):

            if current_user.role == UserRole.COURIER:
                if new_status == OrderStatus.ACCEPTED:
                    if (
                        order.courier_id is not None
                        and order.courier_id != current_user.id
                    ):
                        raise HTTPException(
                            status_code=400,
                            detail="Этот заказ уже принял другой курьер",
                        )
                    order.courier_id = current_user.id

                else:
                    if order.courier_id != current_user.id:
                        raise HTTPException(
                            status_code=403,
                            detail="Вы не можете изменять статус чужого заказа",
                        )

            elif current_user.role == UserRole.CUSTOMER:
                if new_status == OrderStatus.CANCELLED and old_status in [
                    OrderStatus.NEW,
                    OrderStatus.ACCEPTED,
                ]:
                    if order.user_id != current_user.id:
                        raise HTTPException(status_code=403, detail="Это не ваш заказ")
                else:
                    raise HTTPException(
                        status_code=403,
                        detail="У вас нет прав на смену статуса для этого действия",
                    )

        order.status = new_status

        updated_order = await self.order_repo.update(order)
        return updated_order

    async def get_available_orders(self, current_user: User):
        if current_user.role == UserRole.CUSTOMER:
            raise HTTPException(
                status_code=403, detail="У вас нет доступа к списку свободных заказов"
            )

        return await self.order_repo.get_available_orders()
