from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class PriceHistoryBase(BaseModel):
    price: float
    timestamp: datetime

class ProductBase(BaseModel):
    amazon_url: str
    name: str
    image_url: Optional[str] = None
    current_price: float

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime
    price_history: List[PriceHistoryBase] = []

    class Config:
        from_attributes = True

class PriceAlertBase(BaseModel):
    email: str
    target_price: float

class PriceAlertCreate(PriceAlertBase):
    product_id: int

class PriceAlert(PriceAlertBase):
    id: int
    product_id: int
    is_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True 