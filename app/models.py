from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True)
    name = Column(String, nullable=False)
    prices = relationship("Price", back_populates="store")

    def __str__(self):
        return self.name


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    products = relationship("Product", back_populates="category")

    def __str__(self):
        return self.name


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")
    prices = relationship("Price", back_populates="product")

    def __str__(self):
        return self.name


class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    amount = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=True)
    brand = Column(String, nullable=True)
    is_cheapest = Column(Integer, default=0)
    previous_amount = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="prices")
    store = relationship("Store", back_populates="prices")