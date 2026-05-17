"""Tests for inventory transaction logic."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud, schemas
from app.database import Base


def make_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


def seed_user_and_item(db):
    user = crud.create_user(
        db,
        schemas.UserCreate(name="John Smith", employee_id="EMP001", pin="1234"),
    )
    item = crud.create_item(
        db,
        schemas.ItemCreate(
            sku="WRNCH-001",
            item_name="Box of Wrenches",
            description="Box of adjustable wrenches",
        ),
    )
    return user, item


def test_receive_ship_out_and_adjust_update_balance_and_log_transactions():
    db = make_db_session()
    try:
        user, _item = seed_user_and_item(db)

        received = crud.receive_inventory(
            db,
            schemas.InventoryAction(
                sku="WRNCH-001",
                user_id=user.user_id,
                quantity=10,
                notes="Initial shipment received",
            ),
        )
        shipped = crud.ship_out_inventory(
            db,
            schemas.InventoryAction(
                sku="WRNCH-001",
                user_id=user.user_id,
                quantity=3,
                notes="Sent to job site",
            ),
        )
        adjusted = crud.adjust_inventory(
            db,
            schemas.InventoryAdjustment(
                sku="WRNCH-001",
                user_id=user.user_id,
                quantity_change=-2,
                notes="Physical count correction",
            ),
        )

        balance = crud.get_inventory_by_sku(db, "WRNCH-001")
        transactions = crud.get_transactions(db, sku="WRNCH-001")

        assert received.transaction_type == "RECEIVE"
        assert received.quantity_change == 10
        assert received.quantity_before == 0
        assert received.quantity_after == 10
        assert shipped.transaction_type == "SHIP_OUT"
        assert shipped.quantity_change == -3
        assert shipped.quantity_before == 10
        assert shipped.quantity_after == 7
        assert adjusted.transaction_type == "ADJUST"
        assert adjusted.quantity_change == -2
        assert adjusted.quantity_before == 7
        assert adjusted.quantity_after == 5
        assert balance.quantity_on_hand == 5
        assert len(transactions) == 3
    finally:
        db.close()


def test_ship_out_cannot_make_inventory_negative_or_create_transaction():
    db = make_db_session()
    try:
        user, _item = seed_user_and_item(db)

        with pytest.raises(crud.InventoryError):
            crud.ship_out_inventory(
                db,
                schemas.InventoryAction(
                    sku="WRNCH-001",
                    user_id=user.user_id,
                    quantity=1,
                    notes="Too many",
                ),
            )

        balance = crud.get_inventory_by_sku(db, "WRNCH-001")
        assert balance.quantity_on_hand == 0
        assert crud.get_transactions(db) == []
    finally:
        db.close()


def test_inactive_users_cannot_create_inventory_transactions():
    db = make_db_session()
    try:
        user, _item = seed_user_and_item(db)
        user.is_active = False
        db.add(user)
        db.commit()

        with pytest.raises(crud.InventoryError):
            crud.receive_inventory(
                db,
                schemas.InventoryAction(
                    sku="WRNCH-001",
                    user_id=user.user_id,
                    quantity=1,
                ),
            )

        assert crud.get_transactions(db) == []
    finally:
        db.close()


def test_milestone_four_routes_are_registered():
    from app.main import app

    routes = {(route.path, tuple(sorted(route.methods))) for route in app.routes}

    assert ("/inventory", ("GET",)) in routes
    assert ("/inventory/{sku}", ("GET",)) in routes
    assert ("/inventory/receive", ("POST",)) in routes
    assert ("/inventory/ship-out", ("POST",)) in routes
    assert ("/inventory/adjust", ("POST",)) in routes
    assert ("/transactions", ("GET",)) in routes
