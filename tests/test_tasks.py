import pytest
from unittest.mock import AsyncMock, patch
from app.tasks.notifications import notify_order_status_changed_task

from app.models.user import User, UserRole
from app.models.order import Order, OrderStatus
from app.models.value_objects import Dimensions, Weight


@pytest.mark.anyio
@patch("app.tasks.notifications.send_email_async", new_callable=AsyncMock)
async def test_notify_order_status_changed_task_execution(mock_send_email, db_session):
    """Проверяем, что таска вытаскивает данные из БД и корректно триггерит отправку Email."""
    user = User(
        id=10,
        email="worker_test@logitrack.com",
        first_name="Иван",
        last_name="Тестовый",
        role=UserRole.CUSTOMER,
        hashed_password="123",
    )
    order = Order(
        id=550,
        title="Заказ для таски",
        user_id=user.id,
        status=OrderStatus.IN_DELIVERY,
        dimensions=Dimensions(10, 10, 10),
        weight=Weight(500),
        total_price=1000,
        delivery_price=500,
    )
    db_session.add_all([user, order])
    await db_session.commit()

    await notify_order_status_changed_task(
        order_id=550, old_status_name="ACCEPTED", session=db_session
    )

    mock_send_email.assert_called_once()
    kwargs = mock_send_email.call_args.kwargs

    assert kwargs["to_email"] == "worker_test@logitrack.com"
    assert "Заказ №550 обновлен: В доставке" in kwargs["subject"]
    assert "Принят курьером" in kwargs["html_content"]
    assert "В доставке" in kwargs["html_content"]
