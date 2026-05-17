"""SQLAlchemy models for the four-table Inventory MVP schema."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text, func, text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    employee_id = Column(Text, unique=True, nullable=False, index=True)
    pin_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    created_at = Column(DateTime, server_default=func.current_timestamp())

    transactions = relationship("InventoryTransaction", back_populates="user")


class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, index=True)
    sku = Column(Text, unique=True, nullable=False, index=True)
    item_name = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    balance = relationship("InventoryBalance", back_populates="item", uselist=False)
    transactions = relationship("InventoryTransaction", back_populates="item")


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    item_id = Column(Integer, ForeignKey("items.item_id"), primary_key=True)
    quantity_on_hand = Column(Integer, nullable=False, server_default=text("0"))
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    item = relationship("Item", back_populates="balance")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    transaction_type = Column(Text, nullable=False)
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())

    item = relationship("Item", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
