from collections import defaultdict
from datetime import date
from typing import Dict, List

import pytest

import bootstrap
from allocation.adapters import notifications
from allocation.adapters.repository import AbstractRepository
from allocation.domain import commands
from allocation.service_layer import handlers
from allocation.service_layer.unit_of_work import UnitOfWorkProtocol


class FakeProductRepository(AbstractRepository):

    def __init__(self, products) -> None:
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref):
        return next((
            p for p in self._products for b in p.batches
            if b.reference == batchref
        ), None)


class FakeUnitOfWork(UnitOfWorkProtocol):
    def __init__(self):
        self.products = FakeProductRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass

    def __enter__(self):
        return self


class FakeNotifications(notifications.AbstractNotifications):
    def __init__(self):
        self.sent = defaultdict(list)  # type: Dict[str, List[str]]

    def send(self, destination, message):
        self.sent[destination].append(message)


def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        notifications=FakeNotifications(),
        publish=lambda *args: None,
    )


def test_add_batch_for_new_product():
    messagebus = bootstrap_test_app()
    messagebus.handle(
        commands.CreateBatch("batch_ref", "SKU", 100, None))
    assert messagebus.uow.products.get("SKU") is not None
    assert messagebus.uow.committed


def test_add_batch_for_existing_product():
    messagebus = bootstrap_test_app()
    messagebus.handle(commands.CreateBatch("b1", "GARISH-RUG", 100, None))
    messagebus.handle(commands.CreateBatch("b2", "GARISH-RUG", 99, None))

    assert "b2" in [b.reference for b in messagebus.uow.products.get("GARISH-RUG").batches]


def test_returns_allocation():
    messagebus = bootstrap_test_app()
    messagebus.handle(commands.CreateBatch("ref", "sku", 20, None))

    results = messagebus.handle(commands.Allocate("orderid", "sku", 2))
    assert results[0] == "ref"


def test_error_for_invalid_sku():
    messagebus = bootstrap_test_app()

    messagebus.handle(commands.CreateBatch("ref", "sku1", 20, None))

    with pytest.raises(handlers.InvalidSku, match=f"Invalid sku sku"):
        messagebus.handle(commands.Allocate("orderid", "sku2", 2))


def test_commits():
    messagebus = bootstrap_test_app()

    messagebus.handle(commands.CreateBatch("ref", "sku", 20, None))

    messagebus.handle(commands.Allocate("orderid", "sku", 2))
    assert messagebus.uow.committed is True


def test_returns_deallocation():
    messagebus = bootstrap_test_app()
    messagebus.handle(commands.CreateBatch("ref", "sku", 20, None))
    result1 = messagebus.handle(commands.Allocate("orderid", "sku", 2))[0]
    result2 = messagebus.handle(commands.Allocate("orderid", "sku", 2))[0]
    assert result1 == result2


######################
class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        messagebus = bootstrap_test_app()
        messagebus.handle(
            commands.CreateBatch("batch1", "ADORABLE-SETTEE", 100, None))
        [batch] = messagebus.uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100
        messagebus.handle(commands.ChangeBatchQuantity("batch1", 50))
        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        messagebus = bootstrap_test_app()
        event_history = [
            commands.CreateBatch("batch1", "INDIFFERENT-TABLE", 50, None),
            commands.CreateBatch("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            commands.Allocate("order1", "INDIFFERENT-TABLE", 20),
            commands.Allocate("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e)
        [batch1, batch2] = messagebus.uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50
        messagebus.handle(commands.ChangeBatchQuantity("batch1", 25))
        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30


def test_sends_email_on_out_of_stock_error():
    fake_notifs = FakeNotifications()
    bus = bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        notifications=fake_notifs,
        publish=lambda *args: None,
    )
    bus.handle(commands.CreateBatch("b1", "POPULAR-CURTAINS", 9, None))
    bus.handle(commands.Allocate("o1", "POPULAR-CURTAINS", 10))
    assert fake_notifs.sent['stock@made.com'] == [
        f"Out of stock for POPULAR-CURTAINS",
    ]
