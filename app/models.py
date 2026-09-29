from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    stores = relationship("Store", back_populates="owner")
    categories = relationship("Category", back_populates="owner")
    products = relationship("Product", back_populates="owner")

    def __str__(self):
        return self.email


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (UniqueConstraint("owner_id", "number", name="uq_store_owner_number"),)

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    number = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    owner = relationship("User", back_populates="stores")
    prices = relationship("Price", back_populates="store")

    def __str__(self):
        return self.name


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("owner_id", "code", name="uq_category_owner_code"),)

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner = relationship("User", back_populates="categories")
    products = relationship("Product", back_populates="category")

    def __str__(self):
        return self.name


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("owner_id", "category_id", "name", name="uq_product_owner_category_name"),)

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    owner = relationship("User", back_populates="products")
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
