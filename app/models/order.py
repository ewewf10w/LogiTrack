from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, composite, relationship
from app.models.value_objects import Dimensions, Weight
from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    dimensions_width: Mapped[int] = mapped_column()
    dimensions_height: Mapped[int] = mapped_column()
    dimensions_length: Mapped[int] = mapped_column()

    weight_grams: Mapped[int] = mapped_column()

    dimensions: Mapped[Dimensions] = composite(
        Dimensions, "dimensions_width", "dimensions_height", "dimensions_length"
    )

    weight: Mapped[Weight] = composite(Weight, "weight_grams")

    # user: Mapped["User"] = relationship("User", back_populates="orders")

    items: Mapped[list["Item"]] = relationship(
        "Item", secondary="order_items", back_populates="orders"
    )

    version: Mapped[int] = mapped_column(default=1)
