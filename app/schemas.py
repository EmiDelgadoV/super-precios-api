from pydantic import BaseModel, EmailStr
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


# ── AUTENTICACION ─────────────────────────────────────────

class UserCredentials(BaseModel):
    """Se usa tanto para registro como para login: mismo par email + contraseña."""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
