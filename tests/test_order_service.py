import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm.exc import StaleDataError

from app.services.order_service import OrderService
from app.models.user import User, UserRole
from app.models.item import Item
from app.models.order import Order, OrderStatus
from app.schemas.order import (
    OrderCreate,
    OrderFilterParams,
    OrderItemCreate,
    OrderPatch,
)


@pytest.mark.anyio
async def test_create_order_by_courier_raises_forbidden():
    """Проверяем, что курьеры не могут создавать заказы."""
    order_repo = MagicMock()
    item_repo = MagicMock()
    service = OrderService(order_repo=order_repo, item_repo=item_repo)

    courier_user = User(
        id=1, email="c@test.com", first_name="K", last_name="C", role=UserRole.COURIER
    )
    schema = OrderCreate(title="Заказ", items=[])

    with pytest.raises(HTTPException) as exc_info:
        await service.create_order(schema, current_user=courier_user)

    assert exc_info.value.status_code == 403
    assert "Курьеры не могут создавать заказы" in exc_info.value.detail


@pytest.mark.anyio
async def test_create_order_duplicate_items_raises_bad_request():
    """Проверяем запрет на дублирование товаров в разных позициях."""
    order_repo = MagicMock()
    item_repo = MagicMock()
    service = OrderService(order_repo=order_repo, item_repo=item_repo)

    customer = User(
        id=2, email="u@test.com", first_name="I", last_name="I", role=UserRole.CUSTOMER
    )

    schema = OrderCreate(
        title="Тест дубликатов",
        items=[
            OrderItemCreate(item_id=10, quantity=1),
            OrderItemCreate(item_id=10, quantity=2),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_order(schema, current_user=customer)

    assert exc_info.value.status_code == 400
    assert "Запрещено дублирование логических данных" in exc_info.value.detail


@pytest.mark.anyio
async def test_create_order_exceeds_weight_limit():
    """Проверяем триггер валидации на максимальный вес заказа (500 кг)."""
    order_repo = MagicMock()
    item_repo = MagicMock()
    service = OrderService(order_repo=order_repo, item_repo=item_repo)

    customer = User(
        id=2, email="u@test.com", first_name="I", last_name="I", role=UserRole.CUSTOMER
    )

    heavy_item = Item(
        id=1,
        name="Слиток свинца",
        price=1000,
        width=10,
        height=10,
        length=10,
        weight_grams=600000,
    )
    item_repo.get_by_ids = AsyncMock(return_value=[heavy_item])

    schema = OrderCreate(
        title="Тяжелый заказ", items=[OrderItemCreate(item_id=1, quantity=1)]
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_order(schema, current_user=customer)

    assert exc_info.value.status_code == 400
    assert "Превышен лимит веса" in exc_info.value.detail


@pytest.mark.anyio
async def test_change_order_status_invalid_transition_raises_bad_request():
    """Тест State Machine"""
    order_repo = MagicMock()
    item_repo = MagicMock()
    service = OrderService(order_repo=order_repo, item_repo=item_repo)

    customer = User(id=7, email="user@test.com", role=UserRole.CUSTOMER)

    mock_order = Order(id=1, user_id=7, status=OrderStatus.NEW)
    order_repo.get_by_id = AsyncMock(return_value=mock_order)

    with pytest.raises(HTTPException) as exc_info:
        await service.change_order_status(
            order_id=1, new_status=OrderStatus.DELIVERED, current_user=customer
        )

    assert exc_info.value.status_code == 400
    assert "Невозможный перевод статуса" in exc_info.value.detail


@pytest.mark.anyio
async def test_patch_order_optimistic_lock_version_mismatch():
    order_repo = MagicMock()
    item_repo = MagicMock()
    service = OrderService(order_repo=order_repo, item_repo=item_repo)

    customer = User(id=7, email="user@test.com", role=UserRole.CUSTOMER)

    mock_order = Order(id=1, user_id=7, status=OrderStatus.NEW, version=2)
    order_repo.get_by_id = AsyncMock(return_value=mock_order)

    patch_schema = OrderPatch(title="Новое название", version=1)

    with pytest.raises(HTTPException) as exc_info:
        await service.patch_order(
            order_id=1, schema=patch_schema, current_user=customer
        )

    assert exc_info.value.status_code == 409
    assert "Данные устарели" in exc_info.value.detail


@pytest.mark.anyio
async def test_patch_order_optimistic_lock_stale_data_error():
    order_repo = MagicMock()
    item_repo = MagicMock()
    service = OrderService(order_repo=order_repo, item_repo=item_repo)

    customer = User(id=7, email="user@test.com", role=UserRole.CUSTOMER)

    mock_order = Order(id=1, user_id=7, status=OrderStatus.NEW, version=1)
    order_repo.get_by_id = AsyncMock(return_value=mock_order)

    order_repo.update = AsyncMock(side_effect=StaleDataError("Гонка данных"))

    patch_schema = OrderPatch(title="Новое название", version=1)

    with pytest.raises(HTTPException) as exc_info:
        await service.patch_order(
            order_id=1, schema=patch_schema, current_user=customer
        )

    assert exc_info.value.status_code == 409
    assert "изменены другим пользователем при сохранении" in exc_info.value.detail


@pytest.mark.anyio
async def test_get_orders_for_user_filters_by_role():
    order_repo = MagicMock()
    service = OrderService(order_repo=order_repo, item_repo=MagicMock())

    order_repo.get_orders_paginated = AsyncMock(return_value=([], 0))
    params = OrderFilterParams(limit=10, offset=0)

    customer = User(id=5, role=UserRole.CUSTOMER)
    await service.get_orders_for_user(user=customer, params=params)
    order_repo.get_orders_paginated.assert_called_with(params=params, client_id=5)

    courier = User(id=12, role=UserRole.COURIER)
    await service.get_orders_for_user(user=courier, params=params)
    order_repo.get_orders_paginated.assert_called_with(params=params, courier_id=12)

    admin = User(id=1, role=UserRole.ADMIN)
    await service.get_orders_for_user(user=admin, params=params)
    order_repo.get_orders_paginated.assert_called_with(params=params)
