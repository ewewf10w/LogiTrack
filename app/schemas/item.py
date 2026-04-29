from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0, description="Цена в копейках (целое число)")


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
