"""Transaction history routes for the Inventory MVP API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


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


@router.get("", response_model=list[schemas.TransactionDetailRead])
def list_transactions(
    sku: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    """List transaction history, optionally filtered by SKU or user ID."""
    return [
        serialize_transaction(transaction)
        for transaction in crud.get_transactions(db, sku=sku, user_id=user_id)
    ]
