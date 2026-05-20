from fastapi import HTTPException
from sqlalchemy.orm.exc import StaleDataError

from app.models.user import User, UserRole
from app.repositories.item_repo import ItemRepository
from app.repositories.order_repo import OrderRepository
from app.models.order import Order, OrderStatus
from app.models.value_objects import Dimensions, Weight
from app.schemas.order import OrderCreate, OrderPatch


class OrderService:
    def __init__(self, order_repo: OrderRepository, item_repo: ItemRepository):
        self.order_repo = order_repo
        self.item_repo = item_repo

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

        items = await self.item_repo.get_by_ids(schema.item_ids)
        if len(items) != len(schema.item_ids):
            raise HTTPException(
                status_code=404,
                detail="Некоторые из указанных товаров не найдены в системе.",
            )

        manual_dimensions_provided = all(
            v is not None
            for v in [schema.width, schema.height, schema.length, schema.weight_grams]
        )

        if manual_dimensions_provided:
            if any(
                v <= 0
                for v in [
                    schema.width,
                    schema.height,
                    schema.length,
                    schema.weight_grams,
                ]
            ):
                raise HTTPException(
                    status_code=400,
                    detail="Переданные вручную габариты и вес должны быть строго больше нуля.",
                )

            dims = Dimensions(
                width=schema.width, height=schema.height, length=schema.length
            )
            w = Weight(grams=schema.weight_grams)

        else:
            if not items:
                raise HTTPException(
                    status_code=400,
                    detail="Невозможно рассчитать габариты: в заказе нет товаров, и данные не введены вручную.",
                )

            total_weight_grams = sum(item.weight_grams for item in items)

            max_item_width = max(item.width for item in items)
            max_item_length = max(item.length for item in items)

            total_height = sum(item.height for item in items)

            dims = Dimensions(
                width=max_item_width, height=total_height, length=max_item_length
            )
            w = Weight(grams=total_weight_grams)

        if w.kg > 500:
            raise HTTPException(
                status_code=400,
                detail="Суммарный вес груза превышает допустимый лимит компании (500 кг).",
            )

        if dims.volume_m3 > 10:
            raise HTTPException(
                status_code=400,
                detail="Суммарный объем груза превышает лимит вместимости транспорта (10 м³).",
            )

        new_order = Order(
            title=schema.title,
            description=schema.description,
            dimensions=dims,
            weight=w,
            user_id=target_user_id,
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
                )
            )

        if schema.weight_grams is not None:
            order.weight = Weight(grams=schema.weight_grams)

        order.version += 1

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

        try:
            updated_order = await self.order_repo.update(order)
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
