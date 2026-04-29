from pydantic import BaseModel, Field, model_validator
from typing import Optional


class OrderBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="Название заказа")
    description: Optional[str] = Field(
        None, max_length=500, description="Дополнительная информация"
    )

    width: int = Field(..., gt=0, le=1000, description="Ширина в см")
    height: int = Field(..., gt=0, le=1000, description="Высота в см")
    length: int = Field(..., gt=0, le=1000, description="Длина в см")
    weight_grams: int = Field(..., gt=0, le=100000, description="Вес в граммах")


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    id: int
    version: int
    width: int
    height: int
    length: int
    weight_grams: int

    @model_validator(mode="before")
    @classmethod
    def extract_from_value_objects(cls, data):
        if hasattr(data, "dimensions"):
            data.width = data.dimensions.width
            data.height = data.dimensions.height
            data.length = data.dimensions.length

        if hasattr(data, "weight"):
            data.weight_grams = data.weight.grams

        return data

    class Config:
        from_attributes = True
