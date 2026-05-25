from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, composite, relationship
from app.models.order_item import OrderItem
from app.models.value_objects import Dimensions, Weight
from app.db.base import Base
import enum
from sqlalchemy import Enum


class OrderStatus(str, enum.Enum):
    NEW = "Новый"
    ACCEPTED = "Принят курьером"
    IN_DELIVERY = "В доставке"
    DELIVERED = "Доставлен"
    CANCELLED = "Отменен"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    courier_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.NEW, nullable=False
    )

    dimensions_width: Mapped[int] = mapped_column()
    dimensions_height: Mapped[int] = mapped_column()
    dimensions_length: Mapped[int] = mapped_column()

    weight_grams: Mapped[int] = mapped_column()

    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_price: Mapped[int] = mapped_column(Integer, nullable=False)

    @property
    def grand_total(self) -> int:
        return self.total_price + self.delivery_price

    dimensions: Mapped[Dimensions] = composite(
        Dimensions, "dimensions_width", "dimensions_height", "dimensions_length"
    )

    weight: Mapped[Weight] = composite(Weight, "weight_grams")

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="orders"
    )
    courier: Mapped["User"] = relationship(
        "User", foreign_keys=[courier_id], back_populates="courier_orders"
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    version: Mapped[int] = mapped_column(default=1)

    __mapper_args__ = {"version_id_col": version}
