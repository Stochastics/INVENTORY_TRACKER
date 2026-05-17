"""CRUD helpers for the Inventory MVP backend."""

from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_pin, verify_pin


class InventoryError(ValueError):
    """Raised when an inventory transaction violates MVP rules."""


class NotFoundError(ValueError):
    """Raised when a required database row does not exist."""


def get_user_by_employee_id(db: Session, employee_id: str) -> models.User | None:
    """Return a user by employee ID, if one exists."""
    return db.query(models.User).filter(models.User.employee_id == employee_id).first()


def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    """Return a user by primary key, if one exists."""
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create a user while storing only a hashed PIN."""
    db_user = models.User(
        name=user.name,
        employee_id=user.employee_id,
        pin_hash=hash_pin(user.pin),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, employee_id: str, pin: str) -> models.User | None:
    """Return an active user when employee ID and PIN are valid."""
    user = get_user_by_employee_id(db, employee_id)
    if user is None or not user.is_active:
        return None
    if not verify_pin(pin, user.pin_hash):
        return None
    return user


def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    """Create an item and its current inventory balance row."""
    db_item = models.Item(
        sku=item.sku,
        item_name=item.item_name,
        description=item.description,
    )
    db.add(db_item)
    db.flush()

    db.add(models.InventoryBalance(item_id=db_item.item_id, quantity_on_hand=0))
    db.commit()
    db.refresh(db_item)
    return db_item


def get_items(db: Session) -> list[models.Item]:
    """Return all items ordered by SKU."""
    return db.query(models.Item).order_by(models.Item.sku).all()


def get_item_by_sku(db: Session, sku: str) -> models.Item | None:
    """Return an item by SKU, if one exists."""
    return db.query(models.Item).filter(models.Item.sku == sku).first()


def get_or_create_balance(db: Session, item: models.Item) -> models.InventoryBalance:
    """Return an item's inventory balance, creating the zero balance if needed."""
    if item.balance is not None:
        return item.balance

    balance = models.InventoryBalance(item_id=item.item_id, quantity_on_hand=0)
    db.add(balance)
    db.flush()
    db.refresh(item)
    return balance


def get_inventory(db: Session) -> list[models.InventoryBalance]:
    """Return all inventory balances with item data ordered by SKU."""
    return (
        db.query(models.InventoryBalance)
        .join(models.Item)
        .order_by(models.Item.sku)
        .all()
    )


def get_inventory_by_sku(db: Session, sku: str) -> models.InventoryBalance | None:
    """Return the current balance for a SKU, if the item exists."""
    item = get_item_by_sku(db, sku)
    if item is None:
        return None
    return get_or_create_balance(db, item)


def apply_inventory_transaction(
    db: Session,
    *,
    sku: str,
    user_id: int,
    transaction_type: str,
    quantity_change: int,
    notes: str | None = None,
) -> models.InventoryTransaction:
    """Create a transaction row and update the current balance atomically."""
    item = get_item_by_sku(db, sku)
    if item is None:
        raise NotFoundError("sku not found")

    user = get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("user not found")
    if not user.is_active:
        raise InventoryError("inactive users cannot create transactions")

    if transaction_type in {"RECEIVE", "SHIP_OUT"} and quantity_change <= 0:
        raise InventoryError("quantity must be greater than zero")
    if transaction_type == "ADJUST" and quantity_change == 0:
        raise InventoryError("quantity_change cannot be zero")

    balance = get_or_create_balance(db, item)
    quantity_before = balance.quantity_on_hand

    if transaction_type == "RECEIVE":
        signed_change = quantity_change
    elif transaction_type == "SHIP_OUT":
        signed_change = -quantity_change
    elif transaction_type == "ADJUST":
        signed_change = quantity_change
    else:
        raise InventoryError("invalid transaction type")

    quantity_after = quantity_before + signed_change
    if transaction_type == "SHIP_OUT" and quantity_after < 0:
        raise InventoryError("ship-out cannot make inventory negative")

    balance.quantity_on_hand = quantity_after
    transaction = models.InventoryTransaction(
        item_id=item.item_id,
        user_id=user.user_id,
        transaction_type=transaction_type,
        quantity_change=signed_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        notes=notes,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def receive_inventory(
    db: Session, action: schemas.InventoryAction
) -> models.InventoryTransaction:
    """Receive inventory for a SKU."""
    return apply_inventory_transaction(
        db,
        sku=action.sku,
        user_id=action.user_id,
        transaction_type="RECEIVE",
        quantity_change=action.quantity,
        notes=action.notes,
    )


def ship_out_inventory(
    db: Session, action: schemas.InventoryAction
) -> models.InventoryTransaction:
    """Ship inventory out for a SKU."""
    return apply_inventory_transaction(
        db,
        sku=action.sku,
        user_id=action.user_id,
        transaction_type="SHIP_OUT",
        quantity_change=action.quantity,
        notes=action.notes,
    )


def adjust_inventory(
    db: Session, adjustment: schemas.InventoryAdjustment
) -> models.InventoryTransaction:
    """Adjust inventory for a SKU by a signed quantity change."""
    return apply_inventory_transaction(
        db,
        sku=adjustment.sku,
        user_id=adjustment.user_id,
        transaction_type="ADJUST",
        quantity_change=adjustment.quantity_change,
        notes=adjustment.notes,
    )


def get_transactions(
    db: Session,
    *,
    sku: str | None = None,
    user_id: int | None = None,
) -> list[models.InventoryTransaction]:
    """Return transaction history, optionally filtered by SKU and/or user ID."""
    query = db.query(models.InventoryTransaction).join(models.Item)
    if sku is not None:
        query = query.filter(models.Item.sku == sku)
    if user_id is not None:
        query = query.filter(models.InventoryTransaction.user_id == user_id)
    return query.order_by(
        models.InventoryTransaction.created_at.desc(),
        models.InventoryTransaction.transaction_id.desc(),
    ).all()
