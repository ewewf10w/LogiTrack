from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional


class ItemBase(BaseModel):
    id: int
    name: str
    price: int

    model_config = ConfigDict(from_attributes=True)


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
    item_ids: List[int]


class OrderRead(OrderBase):
    id: int
    version: int
    width: int
    height: int
    length: int
    weight_grams: int
    items: List[ItemBase]

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


class OrderPatch(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    length: Optional[int] = Field(None, gt=0)
    weight_grams: Optional[int] = Field(None, gt=0)

    version: int = Field(..., description="Текущая версия заказа")
