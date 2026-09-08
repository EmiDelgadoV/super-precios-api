from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StoreBase(BaseModel):
    number: int
    name: str

class StoreResponse(StoreBase):
    id: int
    model_config = {"from_attributes": True}


class CategoryBase(BaseModel):
    code: str
    name: str

class CategoryResponse(CategoryBase):
    id: int
    model_config = {"from_attributes": True}


class PriceResponse(BaseModel):
    id: int
    store_id: int
    store_name: Optional[str] = None
    amount: float
    unit_price: Optional[float] = None
    quantity: Optional[float] = None
    brand: Optional[str] = None
    is_cheapest: int = 0
    previous_amount: Optional[float] = None
    variation_pct: Optional[float] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str
    category_id: int

class ProductResponse(BaseModel):
    id: int
    name: str
    category: CategoryResponse
    prices: list[PriceResponse] = []
    model_config = {"from_attributes": True}


class PriceUpdate(BaseModel):
    product_id: int
    store_id: int
    amount: float
    brand: Optional[str] = None
    quantity: Optional[float] = None