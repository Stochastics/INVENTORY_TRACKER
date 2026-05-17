"""Tests for bare-bones user creation and login logic."""

from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import verify_pin
from app.routes import auth as auth_routes


def test_create_user_hashes_pin_without_storing_raw_pin(db: Session):
    user = crud.create_user(
        db,
        schemas.UserCreate(name="John Smith", employee_id="EMP001", pin="1234"),
    )

    assert user.pin_hash != "1234"
    assert "1234" not in user.pin_hash
    assert user.pin_hash.startswith("pbkdf2_sha256$")
    assert verify_pin("1234", user.pin_hash)


def test_login_succeeds_with_correct_pin(db: Session):
    crud.create_user(
        db,
        schemas.UserCreate(name="Jane Smith", employee_id="EMP002", pin="2468"),
    )

    response = auth_routes.login(
        schemas.LoginRequest(employee_id="EMP002", pin="2468"), db=db
    )

    assert response.employee_id == "EMP002"
    assert response.name == "Jane Smith"


def test_login_fails_with_wrong_pin(db: Session):
    crud.create_user(
        db,
        schemas.UserCreate(name="Pat Smith", employee_id="EMP003", pin="1357"),
    )

    assert crud.authenticate_user(db, "EMP003", "0000") is None


def test_inactive_user_cannot_log_in(db: Session):
    user = crud.create_user(
        db,
        schemas.UserCreate(name="Alex Smith", employee_id="EMP004", pin="9753"),
    )
    user.is_active = False
    db.add(user)
    db.commit()

    assert crud.authenticate_user(db, "EMP004", "9753") is None
