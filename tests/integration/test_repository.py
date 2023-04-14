import pytest

from allocation.adapters import repository
from allocation.domain import model


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)
    repo = repository.SqlProductRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute("""
        SELECT reference, sku, _purchased_quantity, eta FROM "batches"
    """)
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def insert_order_line(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA"),
    )
    return orderline_id


def insert_batch(session, batch_ref):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        ' VALUES (:batch_id, "GENERIC-SOFA", 100, null)',
        dict(batch_id=batch_ref),
    )
    [[batch_id]] = session.execute(
        'SELECT id FROM batches WHERE reference=:batch_id AND sku="GENERIC-SOFA"',
        dict(batch_id=batch_ref),
    )
    return batch_id


def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id)"
        " VALUES (:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )


@pytest.mark.skip
def test_repository_can_retrieve_a_product_with_allocations(session):
    batch_id = insert_batch(session, "bref_ASD@")
    order_line_id = insert_order_line(session)
    insert_allocation(session, order_line_id, batch_id)

    repo = repository.SqlProductRepository(session)
    retrieved_product = repo.get("GENERIC-SOFA")

    # expected = model.Batch("bref_ASD@", "GENERIC-SOFA", 100, eta=None)
    # assert retrieved_product == expected

    assert retrieved_product.batches[-1]._allocations == {model.OrderLine("order1", "GENERIC-SOFA", 12)}
