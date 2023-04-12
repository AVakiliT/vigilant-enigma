from datetime import date

import pytest

from src.adapters.repository import AbstractRepository
from src.domain import events
from src.service_layer import messagebus, handlers
from src.service_layer.unit_of_work import UnitOfWorkProtocol


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


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()
    messagebus.handle(
        events.BatchCreated("batch_ref", "SKU", 100, None),
        uow
    )
    assert uow.products.get("SKU") is not None
    assert uow.committed


def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    messagebus.handle(events.BatchCreated("b1", "GARISH-RUG", 100, None), uow)
    messagebus.handle(events.BatchCreated("b2", "GARISH-RUG", 99, None), uow)

    assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]


def test_returns_allocation():
    uow = FakeUnitOfWork()
    messagebus.handle(events.BatchCreated("ref", "sku", 20, None), uow)

    results = messagebus.handle(events.AllocationRequired("orderid", "sku", 2), uow)
    assert results[0] == "ref"


def test_error_for_invalid_sku():
    uow = FakeUnitOfWork()

    messagebus.handle(events.BatchCreated("ref", "sku1", 20, None), uow)

    with pytest.raises(handlers.InvalidSku, match=f"Invalid sku sku"):
        messagebus.handle(events.AllocationRequired("orderid", "sku2", 2), uow)


def test_commits():
    uow = FakeUnitOfWork()

    messagebus.handle(events.BatchCreated("ref", "sku", 20, None), uow)

    messagebus.handle(events.AllocationRequired("orderid", "sku", 2), uow)
    assert uow.committed is True


def test_returns_deallocation():
    uow = FakeUnitOfWork()
    messagebus.handle(events.BatchCreated("ref", "sku", 20, None), uow)
    result1 = messagebus.handle(events.AllocationRequired("orderid", "sku", 2), uow=uow)[0]
    result2 = messagebus.handle(events.AllocationRequired("orderid", "sku", 2), uow=uow)[0]
    assert result1 == result2


######################
class TestChangeBatchQuantity:
    def test_changes_available_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            events.BatchCreated("batch1", "ADORABLE-SETTEE", 100, None), uow
        )
        [batch] = uow.products.get(sku="ADORABLE-SETTEE").batches
        assert batch.available_quantity == 100
        messagebus.handle(events.BatchQuantityChanged("batch1", 50), uow)
        assert batch.available_quantity == 50

    def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        event_history = [
            events.BatchCreated("batch1", "INDIFFERENT-TABLE", 50, None),
            events.BatchCreated("batch2", "INDIFFERENT-TABLE", 50, date.today()),
            events.AllocationRequired("order1", "INDIFFERENT-TABLE", 20),
            events.AllocationRequired("order2", "INDIFFERENT-TABLE", 20),
        ]
        for e in event_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku="INDIFFERENT-TABLE").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50
        messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)
        # order1 or order2 will be deallocated, so we'll have 25 - 20
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30
