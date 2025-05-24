from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

from backend import models
from backend import scraper
from backend.database import get_db
from backend.schemas import Product, ProductCreate, PriceHistoryBase, PriceAlertCreate, PriceAlert

router = APIRouter()

class ProductRequest(BaseModel):
    url: str

@router.post("/products/", response_model=Product)
async def create_product(request: ProductRequest, db: Session = Depends(get_db)):
    # Check if product already exists
    existing_product = db.query(models.Product).filter(models.Product.amazon_url == request.url).first()
    if existing_product:
        return existing_product
    
    # Scrape product information
    product_data = scraper.scrape_amazon_product(request.url)
    if not product_data['name'] or not product_data['current_price']:
        raise HTTPException(status_code=400, detail="Could not scrape product information")
    
    # Create new product
    db_product = models.Product(
        amazon_url=request.url,
        name=product_data['name'],
        image_url=product_data['image_url'],
        current_price=product_data['current_price']
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add initial price history
    price_history = models.PriceHistory(
        product_id=db_product.id,
        price=product_data['current_price']
    )
    db.add(price_history)
    db.commit()
    
    return db_product

@router.get("/products/", response_model=List[Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@router.get("/products/{product_id}/price-history", response_model=List[PriceHistoryBase])
def get_price_history(product_id: int, days: int = 30, db: Session = Depends(get_db)):
    start_date = datetime.utcnow() - timedelta(days=days)
    history = db.query(models.PriceHistory)\
        .filter(models.PriceHistory.product_id == product_id)\
        .filter(models.PriceHistory.timestamp >= start_date)\
        .order_by(models.PriceHistory.timestamp)\
        .all()
    
    return history

@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/alerts/", response_model=PriceAlert)
async def create_price_alert(alert: PriceAlertCreate, db: Session = Depends(get_db)):
    # Check if product exists
    product = db.query(models.Product).filter(models.Product.id == alert.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Create new alert
    db_alert = models.PriceAlert(
        product_id=alert.product_id,
        email=alert.email,
        target_price=alert.target_price
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    
    return db_alert 