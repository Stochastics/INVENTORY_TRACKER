"""Item routes for the Inventory MVP API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    """Create an item with a zero current inventory balance."""
    try:
        return crud.create_item(db, item)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="sku already exists",
        ) from exc


@router.get("", response_model=list[schemas.ItemRead])
def list_items(db: Session = Depends(get_db)):
    """List all items."""
    return crud.get_items(db)


@router.get("/{sku}", response_model=schemas.ItemRead)
def get_item(sku: str, db: Session = Depends(get_db)):
    """Get an item by SKU."""
    item = crud.get_item_by_sku(db, sku)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="sku not found"
        )
    return item
