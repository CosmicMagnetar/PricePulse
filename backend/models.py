from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    amazon_url = Column(String, unique=True, index=True)
    name = Column(String)
    image_url = Column(String)
    current_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    price_history = relationship("PriceHistory", back_populates="product")
    price_alerts = relationship("PriceAlert", back_populates="product")
    price_comparisons = relationship("PriceComparison", back_populates="product")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="price_history")

class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    email = Column(String)
    target_price = Column(Float)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="price_alerts")

class PriceComparison(Base):
    __tablename__ = "price_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    flipkart_price = Column(Float, nullable=True)
    flipkart_url = Column(String, nullable=True)
    meesho_price = Column(Float, nullable=True)
    meesho_url = Column(String, nullable=True)
    bigbasket_price = Column(Float, nullable=True)
    bigbasket_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="price_comparisons")

# Create SQLite database
engine = create_engine("sqlite:///./pricepulse.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine) 