from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название товара")
    price: int = Field(..., gt=0, description="Цена товара в копейках")


class ItemCreate(ItemBase):
    width: int = Field(default=10, gt=0, le=1000, description="Ширина товара в см")
    height: int = Field(default=10, gt=0, le=1000, description="Высота товара в см")
    length: int = Field(default=10, gt=0, le=1000, description="Длина товара в см")
    weight_grams: int = Field(
        default=500, gt=0, le=1000000, description="Вес товара в граммах"
    )


class ItemRead(ItemBase):
    id: int
    width: int
    height: int
    length: int
    weight_grams: int

    model_config = ConfigDict(from_attributes=True)
