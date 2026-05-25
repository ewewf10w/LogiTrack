from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from app.models.user import User
from app.task_queue.taskiq_broker import broker
from app.models.db_helper import db_helper
from app.models.order import Order, OrderStatus
from app.core.email_client import send_email_async


@broker.task
async def notify_order_status_changed_task(
    order_id: int,
    old_status_name: str,
    session: Annotated[
        AsyncSession,
        TaskiqDepends(db_helper.session_getter),
    ],
) -> None:
    order = await session.get(Order, order_id)
    if not order:
        print(f"[RABBITMQ WORKER] Ошибка: Заказ №{order_id} не найден в базе данных.")
        return

    user = await session.get(User, order.user_id)
    if not user or not user.email:
        print(f"[RABBITMQ WORKER] Email для пользователя {order.user_id} не найден.")
        return

    old_status = OrderStatus[old_status_name]

    subject = f"Заказ №{order.id} обновлен: {order.status.value}"
    grand_total_rub = order.grand_total / 100

    html_content = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #2c3e50; margin-top: 0; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Уважаемый клиент!</h2>
                <p style="font-size: 16px;">Статус вашего заказа <strong>«{order.title}»</strong> успешно изменился в системе LogiTrack.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 25px 0;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 12px; border: 1px solid #e0e0e0; text-align: left;">Параметр</th>
                            <th style="padding: 12px; border: 1px solid #e0e0e0; text-align: left;">Значение</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;"><strong>Номер заказа:</strong></td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;">№{order.id}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;"><strong>Предыдущий статус:</strong></td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; color: #7f8c8d;">{old_status.value}</td>
                        </tr>
                        <tr style="background-color: #f1f9ff;">
                            <td style="padding: 12px; border: 1px solid #e0e0e0;"><strong>Новый статус:</strong></td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; color: #2980b9; font-weight: bold;">{order.status.value}</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0e0e0;"><strong>Общая стоимость (с доставкой):</strong></td>
                            <td style="padding: 12px; border: 1px solid #e0e0e0; font-weight: bold; color: #27ae60;">{grand_total_rub:,.2f} руб.</td>
                        </tr>
                    </tbody>
                </table>
                
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
                <p style="font-size: 12px; color: #95a5a6; text-align: center; margin-bottom: 0;">
                    Это автоматическое уведомление информационной системы LogiTrack 2026. Отвечать на него не нужно.
                </p>
            </div>
        </body>
    </html>
    """

    await send_email_async(
        to_email=user.email, subject=subject, html_content=html_content
    )
