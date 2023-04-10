from datetime import datetime, timedelta
from typing import List

import pytest

from src.adapters.repository import RepositoryProtocol
from src.domain import model
from src.service_layer import services
from src.service_layer.unit_of_work import UnitOfWorkProtocol


class FakeRepository(RepositoryProtocol):

    def __init__(self) -> None:
        super().__init__()
        self._batches = set()

    def add(self, batch: model.Batch):
        self._batches.add(batch)

    def get(self, reference: str) -> model.Batch:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> List[model.Batch]:
        return list(self._batches)


class FakeUnitOfWork(UnitOfWorkProtocol):
    def __init__(self):
        self.batches = FakeRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def __enter__(self):
        pass


def test_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("ref", "sku", 20, None, uow)

    result = services.allocate("orderid", "sku", 2, uow)
    assert result == "ref"


def test_error_for_invalid_sku():
    uow = FakeUnitOfWork()

    services.add_batch("ref", "sku1", 20, None, uow)

    with pytest.raises(services.InvalidSku, match=f"Invalid sku sku"):
        services.allocate("orderid", "sku2", 2, uow)


def test_commits():
    uow = FakeUnitOfWork()

    services.add_batch("ref", "sku", 20, None, uow)

    services.allocate("orderid", "sku", 2, uow)
    assert uow.committed is True


def test_returns_deallocation():
    uow = FakeUnitOfWork()
    services.add_batch("ref", "sku", 20, None, uow)
    result1 = services.allocate("orderid", "sku", 2, uow=uow)
    result2 = services.deallocate("orderid", "sku", 2, uow=uow)
    assert result1 == result2


######################
today = datetime.today()
tomorrow = datetime.today() + timedelta(days=1)
next_week = datetime.today() + timedelta(days=7)


def test_prefers_current_stock_batches_to_shipments():
    uow = FakeUnitOfWork()
    services.add_batch("in-stock-batch", "sku", 100, None, uow)
    services.add_batch("shipment-batch", "sku", 100, today, uow)

    services.allocate("oref", "sku", 10, uow)
    assert uow.batches.get("in-stock-batch").available_quantity == 90
    assert uow.batches.get("shipment-batch").available_quantity == 100


def test_prefers_earlier_batches():
    uow = FakeUnitOfWork()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, today, uow)
    services.add_batch("shipment-batch-1", "RETRO-CLOCK", 100, tomorrow, uow)
    services.add_batch("shipment-batch-2", "RETRO-CLOCK", 100, next_week, uow)
    services.allocate("oref", "RETRO-CLOCK", 10, uow)

    assert uow.batches.get("in-stock-batch", ).available_quantity == 90
    assert uow.batches.get("shipment-batch-1").available_quantity == 100
    assert uow.batches.get("shipment-batch-2").available_quantity == 100
