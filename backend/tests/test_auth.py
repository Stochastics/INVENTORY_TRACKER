"""Tests for bare-bones user creation and login logic."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud, schemas
from app.database import Base
from app.auth import verify_pin


def make_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


def test_create_user_hashes_pin_without_storing_raw_pin():
    db = make_db_session()
    try:
        user = crud.create_user(
            db,
            schemas.UserCreate(name="John Smith", employee_id="EMP001", pin="1234"),
        )

        assert user.pin_hash != "1234"
        assert user.pin_hash.startswith("pbkdf2_sha256$")
        assert verify_pin("1234", user.pin_hash)
    finally:
        db.close()


def test_authenticate_user_returns_active_user_for_valid_pin():
    db = make_db_session()
    try:
        crud.create_user(
            db,
            schemas.UserCreate(name="Jane Smith", employee_id="EMP002", pin="2468"),
        )

        user = crud.authenticate_user(db, "EMP002", "2468")

        assert user is not None
        assert user.name == "Jane Smith"
        assert user.employee_id == "EMP002"
    finally:
        db.close()


def test_authenticate_user_rejects_wrong_pin_and_inactive_users():
    db = make_db_session()
    try:
        user = crud.create_user(
            db,
            schemas.UserCreate(name="Pat Smith", employee_id="EMP003", pin="1357"),
        )

        assert crud.authenticate_user(db, "EMP003", "0000") is None

        user.is_active = False
        db.add(user)
        db.commit()

        assert crud.authenticate_user(db, "EMP003", "1357") is None
    finally:
        db.close()
