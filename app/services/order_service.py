from typing import List
from fastapi import HTTPException
from sqlalchemy.orm.exc import StaleDataError

from app.models.order_item import OrderItem
from app.models.user import User, UserRole
from app.models.item import Item
from app.repositories.item_repo import ItemRepository
from app.repositories.order_repo import OrderRepository
from app.models.order import Order, OrderStatus
from app.models.value_objects import Dimensions, Weight
from app.schemas.order import OrderCreate, OrderPatch, OrderFilterParams
from app.tasks.notifications import notify_order_status_changed_task
from app.services.notification_service import NotificationService


class OrderService:
    def __init__(
        self, order_repo: OrderRepository, item_repo: ItemRepository, user_manager=None
    ):
        self.order_repo = order_repo
        self.item_repo = item_repo
        self.user_manager = user_manager

    def _calculate_costs(
        self, items_with_qty: List[tuple[Item, int]], weight_kg: float, volume_m3: float
    ):
        total_price = sum(item.price * qty for item, qty in items_with_qty)

        base_fee = 20000
        weight_fee = int(weight_kg * 1000)
        volume_fee = int(volume_m3 * 100 * 5000)

        delivery_price = base_fee + weight_fee + volume_fee
        return total_price, delivery_price

    async def create_order(self, schema: OrderCreate, current_user: User) -> Order:
        if current_user.role == UserRole.COURIER:
            raise HTTPException(
                status_code=403, detail="Курьеры не могут создавать заказы в системе."
            )

        if current_user.role == UserRole.CUSTOMER:
            target_user_id = current_user.id
        elif current_user.role in [UserRole.MANAGER, UserRole.ADMIN]:
            if schema.user_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Менеджер или Администратор обязан указать ID клиента (user_id).",
                )
            target_user_id = schema.user_id
        else:
            raise HTTPException(
                status_code=403, detail="У вашей роли нет прав на создание заказа."
            )

        incoming_item_ids = [pos.item_id for pos in schema.items]
        if len(set(incoming_item_ids)) != len(incoming_item_ids):
            raise HTTPException(
                status_code=400,
                detail="Запрещено дублирование логических данных: один и тот же товар нельзя указывать в разных позициях. Используйте поле quantity.",
            )

        items_from_db = await self.item_repo.get_by_ids(incoming_item_ids)
        if len(items_from_db) != len(incoming_item_ids):
            raise HTTPException(
                status_code=404,
                detail="Некоторые из указанных товаров не найдены в системе.",
            )

        items_dict = {item.id: item for item in items_from_db}

        items_with_qty = [
            (items_dict[pos.item_id], pos.quantity) for pos in schema.items
        ]

        manual_dimensions_provided = all(
            v is not None
            for v in [schema.width, schema.height, schema.length, schema.weight_grams]
        )

        if manual_dimensions_provided:
            dims = Dimensions(
                width=schema.width, height=schema.height, length=schema.length
            )
            w = Weight(grams=schema.weight_grams)
        else:
            if not items_with_qty:
                raise HTTPException(status_code=400, detail="В заказе нет товаров.")

            total_weight_grams = sum(
                item.weight_grams * qty for item, qty in items_with_qty
            )

            dims = Dimensions(
                width=max(item.width for item, _ in items_with_qty),
                height=sum(item.height * qty for item, qty in items_with_qty),
                length=max(item.length for item, _ in items_with_qty),
            )
            w = Weight(grams=total_weight_grams)

        if w.kg > 500:
            raise HTTPException(status_code=400, detail="Превышен лимит веса (500 кг).")
        if dims.volume_m3 > 10:
            raise HTTPException(
                status_code=400, detail="Превышен лимит объема (10 м³)."
            )

        total_price, delivery_price = self._calculate_costs(
            items_with_qty, w.kg, dims.volume_m3
        )

        new_order = Order(
            title=schema.title,
            description=schema.description,
            dimensions=dims,
            weight=w,
            total_price=total_price,
            delivery_price=delivery_price,
            user_id=target_user_id,
        )

        new_order.order_items = [
            OrderItem(item_id=item.id, quantity=qty, order=new_order)
            for item, qty in items_with_qty
        ]

        return await self.order_repo.create(new_order)

    async def get_all_orders(self):
        return await self.order_repo.get_all()

    async def get_orders_for_user(self, user: User, params: OrderFilterParams):
        if user.role in (UserRole.ADMIN, UserRole.MANAGER):
            items, total = await self.order_repo.get_orders_paginated(params=params)

        elif user.role == UserRole.COURIER:
            items, total = await self.order_repo.get_orders_paginated(
                params=params, courier_id=user.id
            )

        else:
            items, total = await self.order_repo.get_orders_paginated(
                params=params, client_id=user.id
            )

        return {
            "orders": items,
            "total": total,
            "limit": params.limit,
            "offset": params.offset,
        }

    async def patch_order(
        self, order_id: int, schema: OrderPatch, current_user: User
    ) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if current_user.role == UserRole.COURIER:
            raise HTTPException(
                status_code=403,
                detail="Курьеры не могут редактировать параметры заказа.",
            )

        if current_user.role == UserRole.CUSTOMER and order.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Вы не можете редактировать чужой заказ."
            )

        if current_user.role == UserRole.CUSTOMER and order.status != OrderStatus.NEW:
            raise HTTPException(
                status_code=400,
                detail=f"Вы можете редактировать заказ только в статусе NEW. Сейчас статус: {order.status.value}",
            )

        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя редактировать заказ в завершенном статусе {order.status.value}",
            )

        if order.version != schema.version:
            raise HTTPException(
                status_code=409,
                detail="Данные устарели. Кто-то другой уже изменил этот заказ. Обновите страницу.",
            )

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

        try:
            return await self.order_repo.update(order)
        except StaleDataError:
            raise HTTPException(
                status_code=409,
                detail="Данные заказа были изменены другим пользователем при сохранении.",
            )

    async def delete_order(self, order_id: int, current_user: User) -> None:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден.")

        if current_user.role == UserRole.COURIER:
            raise HTTPException(
                status_code=403, detail="Курьеры не могут удалять заказы."
            )

        if current_user.role == UserRole.CUSTOMER:
            if order.user_id != current_user.id:
                raise HTTPException(
                    status_code=403, detail="Вы не можете удалить чужой заказ."
                )
            if order.status != OrderStatus.NEW:
                raise HTTPException(
                    status_code=400,
                    detail="Клиент может удалить заказ только на стадии NEW.",
                )

        await self.order_repo.delete(order)

    async def change_order_status(
        self, order_id: int, new_status: OrderStatus, current_user: User
    ) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        old_status = order.status

        if old_status == new_status:
            return order

        if current_user.role in (UserRole.ADMIN, UserRole.MANAGER):
            order.status = new_status
        else:
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
        # -----------------------------------------------------------------

        try:
            updated_order = await self.order_repo.update(order)
            await notify_order_status_changed_task.kiq(
                order_id=updated_order.id,
                old_status_name=old_status.name,
            )

            return updated_order

        except StaleDataError:
            raise HTTPException(
                status_code=409,
                detail="Данные заказа были изменены другим пользователем. Пожалуйста, обновите страницу.",
            )

    async def get_available_orders(self, current_user: User):
        if current_user.role == UserRole.CUSTOMER:
            raise HTTPException(
                status_code=403, detail="У вас нет доступа к списку свободных заказов"
            )

        return await self.order_repo.get_available_orders()

    async def assign_courier(
        self, order_id: int, courier_id: int, current_user: User
    ) -> Order:
        if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(status_code=403, detail="Нет прав.")

        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден.")

        courier = None
        if self.user_manager:
            try:
                courier = await self.user_manager.get(courier_id)
            except Exception:
                pass

        if not courier or courier.role != UserRole.COURIER:
            raise HTTPException(
                status_code=400,
                detail="Пользователь не найден или не является курьером.",
            )

        order.courier_id = courier.id
        if order.status == OrderStatus.NEW:
            order.status = OrderStatus.ACCEPTED

        return await self.order_repo.update(order)
