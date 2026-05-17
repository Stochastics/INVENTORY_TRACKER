"""CRUD helpers for the Inventory MVP backend."""

from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_pin, verify_pin


def get_user_by_employee_id(db: Session, employee_id: str) -> models.User | None:
    """Return a user by employee ID, if one exists."""
    return db.query(models.User).filter(models.User.employee_id == employee_id).first()


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
