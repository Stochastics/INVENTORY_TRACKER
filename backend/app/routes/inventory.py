"""Inventory balance and transaction routes for the Inventory MVP API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])


def serialize_inventory(balance: models.InventoryBalance) -> schemas.InventoryRead:
    """Build the inventory API response with item details and current quantity."""
    return schemas.InventoryRead(
        item_id=balance.item_id,
        sku=balance.item.sku,
        item_name=balance.item.item_name,
        description=balance.item.description,
        quantity_on_hand=balance.quantity_on_hand,
        updated_at=balance.updated_at,
    )


def handle_inventory_error(exc: ValueError) -> None:
    """Convert inventory domain errors into API responses."""
    if isinstance(exc, crud.NotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[schemas.InventoryRead])
def list_inventory(db: Session = Depends(get_db)):
    """List current inventory balances for all items."""
    return [serialize_inventory(balance) for balance in crud.get_inventory(db)]


@router.get("/{sku}", response_model=schemas.InventoryRead)
def get_inventory(sku: str, db: Session = Depends(get_db)):
    """Get current inventory for one SKU."""
    balance = crud.get_inventory_by_sku(db, sku)
    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="sku not found"
        )
    return serialize_inventory(balance)


@router.post(
    "/receive",
    response_model=schemas.TransactionDetailRead,
    status_code=status.HTTP_201_CREATED,
)
def receive_inventory(action: schemas.InventoryAction, db: Session = Depends(get_db)):
    """Receive inventory and record the transaction."""
    try:
        return serialize_transaction(crud.receive_inventory(db, action))
    except ValueError as exc:
        handle_inventory_error(exc)


@router.post(
    "/ship-out",
    response_model=schemas.TransactionDetailRead,
    status_code=status.HTTP_201_CREATED,
)
def ship_out_inventory(action: schemas.InventoryAction, db: Session = Depends(get_db)):
    """Ship inventory out and record the transaction."""
    try:
        return serialize_transaction(crud.ship_out_inventory(db, action))
    except ValueError as exc:
        handle_inventory_error(exc)


@router.post(
    "/adjust",
    response_model=schemas.TransactionDetailRead,
    status_code=status.HTTP_201_CREATED,
)
def adjust_inventory(action: schemas.InventoryAdjustment, db: Session = Depends(get_db)):
    """Adjust inventory and record the transaction."""
    try:
        return serialize_transaction(crud.adjust_inventory(db, action))
    except ValueError as exc:
        handle_inventory_error(exc)


def serialize_transaction(
    transaction: models.InventoryTransaction,
) -> schemas.TransactionDetailRead:
    """Build a transaction API response with SKU, item name, and user name."""
    return schemas.TransactionDetailRead(
        transaction_id=transaction.transaction_id,
        item_id=transaction.item_id,
        user_id=transaction.user_id,
        transaction_type=transaction.transaction_type,
        quantity_change=transaction.quantity_change,
        quantity_before=transaction.quantity_before,
        quantity_after=transaction.quantity_after,
        notes=transaction.notes,
        created_at=transaction.created_at,
        sku=transaction.item.sku,
        item_name=transaction.item.item_name,
        user_name=transaction.user.name,
    )
