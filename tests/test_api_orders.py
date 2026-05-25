import pytest
from httpx import AsyncClient
from app.main import app
from app.authentication.fastapi_users import current_active_user
from app.models import User, UserRole, Item, Order
from sqlalchemy import select

fake_customer = User(
    id=42,
    email="customer@logitrack.ru",
    first_name="Алексей",
    last_name="Петров",
    role=UserRole.CUSTOMER,
    is_active=True,
    hashed_password="fake",
)


async def override_current_user():
    return fake_customer


@pytest.mark.anyio
async def test_api_create_order_success(client: AsyncClient, db_session):
    """Интеграционный тест: создание заказа через API эндпоинт."""
    app.dependency_overrides[current_active_user] = override_current_user

    test_item = Item(
        id=100,
        name="Коробка передач",
        price=500000,
        width=30,
        height=30,
        length=40,
        weight_grams=15000,
    )
    db_session.add(test_item)
    await db_session.commit()

    order_payload = {
        "title": "Доставка КПП",
        "description": "Срочно на СТО",
        "items": [{"item_id": 100, "quantity": 1}],
    }

    response = await client.post("/orders/", json=order_payload)

    assert response.status_code == 201
    resp_data = response.json()
    assert resp_data["title"] == "Доставка КПП"
    assert resp_data["status"] == "Новый"
    assert resp_data["user_id"] == 42
    assert resp_data["grand_total"] > 0

    db_result = await db_session.execute(select(Order).filter_by(title="Доставка КПП"))
    db_order = db_result.scalar_one_or_none()
    assert db_order is not None
    assert db_order.total_price == 500000

    del app.dependency_overrides[current_active_user]
