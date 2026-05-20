from sqlalchemy import Table, Column, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    width: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10", nullable=False
    )
    height: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10", nullable=False
    )
    length: Mapped[int] = mapped_column(
        Integer, default=10, server_default="10", nullable=False
    )
    weight_grams: Mapped[int] = mapped_column(
        Integer, default=500, server_default="500", nullable=False
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order", secondary="order_items", back_populates="items"
    )
