import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.services.order_service import OrderService
from app.models.user import User, UserRole
from app.models.item import Item
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderItemCreate


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
