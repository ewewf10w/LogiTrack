from sqlalchemy import Table, Column, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(Integer)

    orders: Mapped[list["Order"]] = relationship(
        "Order", secondary="order_items", back_populates="items"
    )
