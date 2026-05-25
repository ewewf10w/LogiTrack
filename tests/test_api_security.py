import pytest
from httpx import AsyncClient
from app.main import app
from app.authentication.fastapi_users import current_active_user
from app.models.user import User, UserRole  # Подставь свои правильные импорты моделей


async def override_current_user_as_courier():
    return User(
        id=999,
        email="courier@logitrack.com",
        role=UserRole.COURIER,
        is_active=True,
        is_verified=True,
    )


@pytest.mark.anyio
async def test_api_create_order_by_courier_returns_403(client: AsyncClient):
    app.dependency_overrides[current_active_user] = override_current_user_as_courier

    order_payload = {
        "title": "Заказ от курьера",
        "items": [{"item_id": 100, "quantity": 1}],
    }

    response = await client.post("/orders/", json=order_payload)

    app.dependency_overrides.clear()

    assert response.status_code == 403
