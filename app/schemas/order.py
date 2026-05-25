from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional
from app.models.order import OrderStatus
from app.schemas.item import ItemRead


class ItemBase(BaseModel):
    id: int
    name: str
    price: int

    model_config = ConfigDict(from_attributes=True)


class OrderItemCreate(BaseModel):
    item_id: int = Field(..., gt=0, description="ID товара")
    quantity: int = Field(default=1, gt=0, le=100, description="Количество штук")


class OrderItemRead(BaseModel):
    quantity: int
    item: ItemRead = Field(..., description="Данные самого товара")

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="Название заказа")
    description: Optional[str] = Field(
        None, max_length=500, description="Дополнительная информация"
    )


class OrderCreate(OrderBase):
    """Схема для создания заказа"""

    items: List[OrderItemCreate] = Field(
        ..., description="Список позиций (товаров и их количества) в заказе"
    )
    user_id: Optional[int] = Field(
        default=None, description="ID клиента, если заказ создается менеджером"
    )

    width: Optional[int] = Field(None, gt=0, le=1000, description="Ширина в см")
    height: Optional[int] = Field(None, gt=0, le=1000, description="Высота в см")
    length: Optional[int] = Field(None, gt=0, le=1000, description="Длина в см")
    weight_grams: Optional[int] = Field(
        None, gt=0, le=1000000, description="Вес в граммах"
    )


class OrderRead(OrderBase):
    id: int
    status: OrderStatus
    version: int

    width: int
    height: int
    length: int
    weight_grams: int

    user_id: Optional[int] = None
    courier_id: Optional[int] = None

    items: List[OrderItemRead]

    volume_m3: float
    weight_kg: float

    total_price: int
    delivery_price: int
    grand_total: int

    @model_validator(mode="before")
    @classmethod
    def extract_from_value_objects(cls, data):
        if hasattr(data, "order_items") and data.order_items is not None:
            data.items = data.order_items

        if hasattr(data, "dimensions") and data.dimensions is not None:
            data.width = data.dimensions.width
            data.height = data.dimensions.height
            data.length = data.dimensions.length
            data.volume_m3 = data.dimensions.volume_m3

        if hasattr(data, "weight") and data.weight is not None:
            data.weight_grams = data.weight.grams
            data.weight_kg = data.weight.kg

        return data

    model_config = ConfigDict(from_attributes=True)


class OrderPatch(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None

    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    length: Optional[int] = Field(None, gt=0)
    weight_grams: Optional[int] = Field(None, gt=0)

    version: int = Field(..., description="Текущая версия заказа")


class OrderAssignCourier(BaseModel):
    courier_id: int


class OrderFilterParams(BaseModel):
    limit: int = Field(
        default=10, ge=1, le=100, description="Количество элементов на странице"
    )
    offset: int = Field(
        default=0, ge=0, description="Смещение (пропустить N элементов)"
    )
    status: Optional[OrderStatus] = Field(
        default=None, description="Фильтрация по статусу заказа"
    )
    sort_by: str = Field(
        default="-id",
        description="Сортировка, например: 'id' (возрастание) или '-id' (убывание)",
    )


class OrderPaginationResponse(BaseModel):
    items: List[OrderRead] = Field(
        ..., description="Список заказов на текущей странице"
    )
    total: int = Field(
        ..., description="Общее количество заказов, соответствующих фильтру"
    )
    limit: int = Field(..., description="Текущий лимит")
    offset: int = Field(..., description="Текущее смещение")

    model_config = ConfigDict(from_attributes=True)
