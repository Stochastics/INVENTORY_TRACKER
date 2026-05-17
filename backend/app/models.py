"""SQLAlchemy models for the four-table Inventory MVP schema."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, TIMESTAMP, Text, text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"sqlite_autoincrement": True}

    user_id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    employee_id = Column(Text, unique=True, nullable=False)
    pin_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, server_default=text("1"))
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    transactions = relationship("InventoryTransaction", back_populates="user")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = {"sqlite_autoincrement": True}

    item_id = Column(Integer, primary_key=True)
    sku = Column(Text, unique=True, nullable=False)
    item_name = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    balance = relationship("InventoryBalance", back_populates="item", uselist=False)
    transactions = relationship("InventoryTransaction", back_populates="item")


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    item_id = Column(Integer, ForeignKey("items.item_id"), primary_key=True)
    quantity_on_hand = Column(Integer, nullable=False, server_default=text("0"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship("Item", back_populates="balance")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = {"sqlite_autoincrement": True}

    transaction_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.item_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    transaction_type = Column(Text, nullable=False)
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship("Item", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
