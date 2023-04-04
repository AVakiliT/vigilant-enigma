import pytest
from sqlalchemy.orm import Session

from src import model


def test_orderline_mapper_can_load_lines(session: Session):
    session.execute("""
        insert into order_lines (orderid, sku, qty) values 
        ("order1", "RED-CHAIR", 12),
        ("order1", "RED-TABLE", 12),
        ("order1", "BLUE-LIPSTICK", 12)
    """)

    expected = [
        model.OrderLine("order1", "RED-CHAIR", 12),
        model.OrderLine("order1", "RED-TABLE", 12),
        model.OrderLine("order1", "BLUE-LIPSTICK", 12)
    ]

    actual = session.query(model.OrderLine).all()
    print(actual)

    assert session.query(model.OrderLine).all() == expected


@pytest.mark.skip
def test_orderline_mapper_can_save_lines(session):
    pass


@pytest.mark.skip
def test_retrieving_batches(session):
    pass


@pytest.mark.skip
def test_saving_batches(session):
    pass


@pytest.mark.skip
def test_saving_allocations(session):
    pass


@pytest.mark.skip
def test_retrieving_allocations(session):
    pass
