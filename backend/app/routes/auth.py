"""Login routes for the Inventory MVP API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate an active user with employee ID and PIN."""
    user = crud.authenticate_user(db, credentials.employee_id, credentials.pin)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid employee_id or pin",
        )
    return user
