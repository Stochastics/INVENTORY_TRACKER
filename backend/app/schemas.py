"""Pydantic schemas for Inventory MVP request and response shapes."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    name: str
    employee_id: str


class UserCreate(UserBase):
    pin: str


class UserRead(UserBase):
    user_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    employee_id: str
    pin: str


class LoginResponse(UserBase):
    user_id: int


class ItemBase(BaseModel):
    sku: str
    item_name: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    item_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryBalanceRead(BaseModel):
    item_id: int
    quantity_on_hand: int
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryAction(BaseModel):
    sku: str
    user_id: int
    quantity: int
    notes: Optional[str] = None


class InventoryAdjustment(BaseModel):
    sku: str
    user_id: int
    quantity_change: int
    notes: Optional[str] = None


class TransactionRead(BaseModel):
    transaction_id: int
    item_id: int
    user_id: int
    transaction_type: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
