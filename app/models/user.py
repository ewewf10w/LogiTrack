import enum

from typing import TYPE_CHECKING
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable

if TYPE_CHECKING:
    from app.models.order import Order


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CUSTOMER = "customer"
    COURIER = "courier"


class User(Base, SQLAlchemyBaseUserTable[int]):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.CUSTOMER, nullable=False
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order", foreign_keys="[Order.user_id]", back_populates="user"
    )

    courier_orders: Mapped[list["Order"]] = relationship(
        "Order", foreign_keys="[Order.courier_id]", back_populates="courier"
    )

    def __repr__(self):
        return f"<User {self.email} (Role: {self.role})>"
