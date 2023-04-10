import pytest

from src.domain import model
from src.service_layer import unit_of_work


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        """INSERT INTO batches (reference, sku, _purchased_quantity, eta)
 VALUES (:ref, :sku, :qty, :eta)""",
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )


def get_allocated_batch_ref(session, orderid, sku):
    [[orderline_id]] = session.execute(
        """select id from order_lines where orderid=:orderid and sku=:sku""",
        dict(orderid=orderid, sku=sku)
    )
    [[batch_ref]] = session.execute(
        f"""select reference from
         allocations join batches b on allocations.batch_id = b.id
          where orderline_id = :orderid""",
        dict(orderid=orderline_id)
    )
    return batch_ref


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, 'ref', 'sku', 100, None)

    session = session_factory()
    rows = list(session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    uow = unit_of_work.SqlUnitOfWork(session_factory)

    class DummyException(Exception):
        pass

    with pytest.raises(DummyException):
        with uow:
            insert_batch(uow.session, 'ref', 'sku', 100, None)
            raise DummyException

    session = session_factory()
    rows = list(session.execute('SELECT * FROM "batches"'))
    assert rows == []

def  test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    session = session_factory()
    insert_batch(session, 'batch1', 'HIPSTER-WORKBENCH', 100, None)
    session.commit()

    uow = unit_of_work.SqlUnitOfWork(session_factory)
    with uow:
        batch = uow.batches.get(reference='batch1')
        line = model.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
        batch.allocate(line)
        uow.commit()
    batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
    assert batchref == 'batch1'