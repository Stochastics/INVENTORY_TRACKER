"""Tests for inventory item, balance, transaction, and API behavior."""

import pytest
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.routes import inventory as inventory_routes
from app.routes import transactions as transaction_routes


def seed_user_and_item(
    db: Session,
    *,
    employee_id: str = "EMP001",
    sku: str = "WRNCH-001",
) -> tuple[models.User, models.Item]:
    user = crud.create_user(
        db,
        schemas.UserCreate(name="John Smith", employee_id=employee_id, pin="1234"),
    )
    item = crud.create_item(
        db,
        schemas.ItemCreate(
            sku=sku,
            item_name="Box of Wrenches",
            description="Box of adjustable wrenches",
        ),
    )
    return user, item


def test_create_item_creates_zero_inventory_balance(db: Session):
    _user, item = seed_user_and_item(db)

    balance = crud.get_inventory_by_sku(db, item.sku)

    assert balance is not None
    assert balance.item_id == item.item_id
    assert balance.quantity_on_hand == 0


def test_receive_inventory_increases_balance_and_creates_transaction(db: Session):
    user, _item = seed_user_and_item(db)

    transaction = crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=10),
    )

    balance = crud.get_inventory_by_sku(db, "WRNCH-001")
    assert balance.quantity_on_hand == 10
    assert transaction.transaction_type == "RECEIVE"
    assert transaction.quantity_change == 10
    assert transaction.quantity_before == 0
    assert transaction.quantity_after == 10
    assert db.query(models.InventoryTransaction).count() == 1


def test_ship_out_decreases_balance(db: Session):
    user, _item = seed_user_and_item(db)
    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=10),
    )

    transaction = crud.ship_out_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=3),
    )

    balance = crud.get_inventory_by_sku(db, "WRNCH-001")
    assert balance.quantity_on_hand == 7
    assert transaction.transaction_type == "SHIP_OUT"
    assert transaction.quantity_change == -3
    assert transaction.quantity_before == 10
    assert transaction.quantity_after == 7


def test_ship_out_cannot_make_inventory_negative_or_create_transaction(db: Session):
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


def test_adjust_can_increase_inventory(db: Session):
    user, _item = seed_user_and_item(db)

    transaction = crud.adjust_inventory(
        db,
        schemas.InventoryAdjustment(
            sku="WRNCH-001", user_id=user.user_id, quantity_change=4
        ),
    )

    balance = crud.get_inventory_by_sku(db, "WRNCH-001")
    assert balance.quantity_on_hand == 4
    assert transaction.transaction_type == "ADJUST"
    assert transaction.quantity_change == 4
    assert transaction.quantity_before == 0
    assert transaction.quantity_after == 4


def test_adjust_can_decrease_inventory(db: Session):
    user, _item = seed_user_and_item(db)
    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=10),
    )

    transaction = crud.adjust_inventory(
        db,
        schemas.InventoryAdjustment(
            sku="WRNCH-001", user_id=user.user_id, quantity_change=-2
        ),
    )

    balance = crud.get_inventory_by_sku(db, "WRNCH-001")
    assert balance.quantity_on_hand == 8
    assert transaction.transaction_type == "ADJUST"
    assert transaction.quantity_change == -2
    assert transaction.quantity_before == 10
    assert transaction.quantity_after == 8


def test_every_inventory_change_creates_transaction_with_correct_before_and_after(
    db: Session,
):
    user, _item = seed_user_and_item(db)

    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=10),
    )
    crud.ship_out_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=3),
    )
    crud.adjust_inventory(
        db,
        schemas.InventoryAdjustment(
            sku="WRNCH-001", user_id=user.user_id, quantity_change=-2
        ),
    )

    transactions = (
        db.query(models.InventoryTransaction)
        .order_by(models.InventoryTransaction.transaction_id)
        .all()
    )
    assert [transaction.transaction_type for transaction in transactions] == [
        "RECEIVE",
        "SHIP_OUT",
        "ADJUST",
    ]
    assert [transaction.quantity_before for transaction in transactions] == [0, 10, 7]
    assert [transaction.quantity_after for transaction in transactions] == [10, 7, 5]


def test_inactive_users_cannot_create_inventory_transactions(db: Session):
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


def test_get_inventory_returns_current_balances(db: Session):
    user, _item = seed_user_and_item(db)
    crud.create_item(
        db,
        schemas.ItemCreate(sku="BOLT-001", item_name="Box of Bolts"),
    )
    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=5),
    )

    response = inventory_routes.list_inventory(db=db)

    balances = {row.sku: row.quantity_on_hand for row in response}
    assert balances == {"BOLT-001": 0, "WRNCH-001": 5}


def test_get_inventory_sku_returns_one_item_balance(db: Session):
    user, _item = seed_user_and_item(db)
    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=5),
    )

    response = inventory_routes.get_inventory("WRNCH-001", db=db)

    assert response.sku == "WRNCH-001"
    assert response.quantity_on_hand == 5


def test_get_transactions_returns_transaction_history(db: Session):
    user, _item = seed_user_and_item(db)
    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=8),
    )
    crud.ship_out_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=2),
    )

    response = transaction_routes.list_transactions(db=db)

    assert [row.transaction_type for row in response] == ["SHIP_OUT", "RECEIVE"]
    assert [row.quantity_after for row in response] == [6, 8]


def test_get_transactions_filters_by_sku(db: Session):
    user, _item = seed_user_and_item(db)
    crud.create_item(
        db,
        schemas.ItemCreate(sku="BOLT-001", item_name="Box of Bolts"),
    )
    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="WRNCH-001", user_id=user.user_id, quantity=8),
    )
    crud.receive_inventory(
        db,
        schemas.InventoryAction(sku="BOLT-001", user_id=user.user_id, quantity=2),
    )

    response = transaction_routes.list_transactions(sku="WRNCH-001", db=db)

    assert len(response) == 1
    assert response[0].sku == "WRNCH-001"


def test_get_transactions_filters_by_user(db: Session):
    first_user, _item = seed_user_and_item(db)
    second_user = crud.create_user(
        db,
        schemas.UserCreate(name="Jane Smith", employee_id="EMP002", pin="2468"),
    )
    crud.receive_inventory(
        db,
        schemas.InventoryAction(
            sku="WRNCH-001", user_id=first_user.user_id, quantity=8
        ),
    )
    crud.receive_inventory(
        db,
        schemas.InventoryAction(
            sku="WRNCH-001", user_id=second_user.user_id, quantity=2
        ),
    )

    response = transaction_routes.list_transactions(
        user_id=second_user.user_id, db=db
    )

    assert len(response) == 1
    assert response[0].user_id == second_user.user_id


def test_milestone_four_routes_are_registered():
    from app.main import app

    routes = {(route.path, tuple(sorted(route.methods))) for route in app.routes}

    assert ("/inventory", ("GET",)) in routes
    assert ("/inventory/{sku}", ("GET",)) in routes
    assert ("/inventory/receive", ("POST",)) in routes
    assert ("/inventory/ship-out", ("POST",)) in routes
    assert ("/inventory/adjust", ("POST",)) in routes
    assert ("/transactions", ("GET",)) in routes
