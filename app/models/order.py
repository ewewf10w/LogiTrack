from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, composite
from sqlalchemy.orm import DeclarativeBase
from app.models.value_objects import Dimensions, Weight


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(nullable=True)

    dimensions_width: Mapped[int] = mapped_column()
    dimensions_height: Mapped[int] = mapped_column()
    dimensions_length: Mapped[int] = mapped_column()

    weight_grams: Mapped[int] = mapped_column()

    dimensions: Mapped[Dimensions] = composite(
        Dimensions, "dimensions_width", "dimensions_height", "dimensions_length"
    )

    weight: Mapped[Weight] = composite(Weight, "weight_grams")

    version: Mapped[int] = mapped_column(default=1)
