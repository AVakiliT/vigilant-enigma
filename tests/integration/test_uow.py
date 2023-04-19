import threading
import time
import traceback
from typing import List

import pytest

from allocation.domain import model
from allocation.service_layer import unit_of_work
from ..random_refs import random_sku, random_batchref, random_orderid


def insert_batch(session, ref, sku, qty, eta, product_version=1):
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version)",
        dict(sku=sku, version=product_version),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
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


def test_rolls_back_uncommitted_work_by_default(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        insert_batch(uow.session, 'ref', 'sku_123123', 100, None)

    session = sqlite_session_factory()
    rows = list(session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)

    class DummyException(Exception):
        pass

    with pytest.raises(DummyException):
        with uow:
            insert_batch(uow.session, 'ref', 'sku', 100, None)
            raise DummyException

    session = sqlite_session_factory()
    rows = list(session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_uow_can_retrieve_a_batch_and_allocate_to_it(sqlite_session_factory):
    session = sqlite_session_factory()
    insert_batch(session, 'batch1', 'HIPSTER-WORKBENCH', 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        batch = uow.products.get('HIPSTER-WORKBENCH').batches[-1]
        line = model.OrderLine('o1', 'HIPSTER-WORKBENCH', 10)
        batch.allocate(line)
        uow.commit()
    batchref = get_allocated_batch_ref(session, 'o1', 'HIPSTER-WORKBENCH')
    assert batchref == 'batch1'


#########
def try_to_allocate(orderid, sku, exceptions, ref, session_factory):
    line = model.OrderLine(orderid, sku, 10)
    try:
        with unit_of_work.SqlAlchemyUnitOfWork(session_factory) as uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            ref[0] = list(product.batches[0]._allocations)[0].orderid
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


def test_concurrent_updates_to_version_are_not_allowed(postgres_session_factory):
    sku, batch = random_sku(), random_batchref()
    session = postgres_session_factory()
    insert_batch(session, batch, sku, 100, eta=None, product_version=1)
    session.commit()

    order1, order2 = random_orderid(1), random_orderid(2)
    exceptions = []  # type: List[Exception]
    ref1 = [None]
    ref2 = [None]
    try_to_allocate_order1 = lambda: try_to_allocate(order1, sku, exceptions, ref1, postgres_session_factory)
    try_to_allocate_order2 = lambda: try_to_allocate(order2, sku, exceptions, ref2, postgres_session_factory)
    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[version]] = session.execute(
        "SELECT version_number FROM products WHERE sku=:sku",
        dict(sku=sku),
    )
    assert version == 2
    assert len(exceptions) == 1

    orders = session.execute(
        "SELECT orderid FROM allocations"
        " JOIN batches ON allocations.batch_id = batches.id"
        " JOIN order_lines ON allocations.orderline_id = order_lines.id"
        " WHERE order_lines.sku=:sku",
        dict(sku=sku),
    )
    assert orders.rowcount == 1
    with unit_of_work.SqlAlchemyUnitOfWork() as uow:
        uow.session.execute("select 1")
