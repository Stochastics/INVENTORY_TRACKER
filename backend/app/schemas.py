"""Pydantic schemas for Inventory MVP request and response shapes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    name: str
    employee_id: str


class UserCreate(UserBase):
    pin: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    pin_hash: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    employee_id: str
    pin: str


class LoginResponse(UserBase):
    user_id: int


class ItemBase(BaseModel):
    sku: str
    item_name: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    created_at: datetime


class InventoryBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    quantity_on_hand: int
    updated_at: datetime


class InventoryAction(BaseModel):
    sku: str
    user_id: int
    quantity: int
    notes: str | None = None


class InventoryAdjustment(BaseModel):
    sku: str
    user_id: int
    quantity_change: int
    notes: str | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    item_id: int
    user_id: int
    transaction_type: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    notes: str | None = None
    created_at: datetime
