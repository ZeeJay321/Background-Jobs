import enum
from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, ForeignKey, Enum, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class SizeEnum(enum.Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"

class OrderStatusEnum(enum.Enum):
    PENDING = "PENDING"
    FAILED = "FAILED"
    PAID = "PAID"
    SHIPPED = "SHIPPED"

# --- Models ---
class User(Base):
    __tablename__ = "User"

    id = Column(String, primary_key=True)
    fullname = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phoneNumber = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    resetToken = Column(String, unique=True, nullable=True)
    resetTokenExpiresAt = Column(DateTime, nullable=True)
    stripeCustomerId = Column(String, unique=True, nullable=True)

    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = "Product"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    isDeleted = Column(Boolean, default=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    variants = relationship("ProductVariant", back_populates="product")
    orderItems = relationship("OrderItem", back_populates="product")


class ProductVariant(Base):
    __tablename__ = "ProductVariant"
    __table_args__ = (UniqueConstraint("productId", "color", "size"),)

    id = Column(String, primary_key=True)
    productId = Column(String, ForeignKey("Product.id"))
    color = Column(String, nullable=False)
    colorCode = Column(String, nullable=True)
    size = Column(Enum(SizeEnum), nullable=False)
    img = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    isDeleted = Column(Boolean, default=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    product = relationship("Product", back_populates="variants")
    orderItems = relationship("OrderItem", back_populates="variant")


class Order(Base):
    __tablename__ = "Order"

    id = Column(String, primary_key=True)
    orderNumber = Column(Integer, unique=True)
    userId = Column(String, ForeignKey("User.id"))
    amount = Column(Float, nullable=False)
    date = Column(String, nullable=False)
    orderStatus = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    sessionId = Column(String, unique=True, nullable=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="orders")
    products = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "OrderItem"

    id = Column(String, primary_key=True)
    orderId = Column(String, ForeignKey("Order.id"))
    productId = Column(String, ForeignKey("Product.id"), nullable=True)
    variantId = Column(String, ForeignKey("ProductVariant.id"), nullable=True)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="products")
    product = relationship("Product", back_populates="orderItems")
    variant = relationship("ProductVariant", back_populates="orderItems")

class OrderSummary(Base):
    __tablename__ = "OrderSummary"

    id = Column(String, primary_key=True)
    totalOrders = Column(Integer, nullable=False)
    totalProductsInOrders = Column(Integer, nullable=False)
    totalOrderAmount = Column(Float, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())