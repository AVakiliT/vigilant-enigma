from datetime import datetime, timedelta
from typing import List, Set

import pytest

from src.adapters.repository import RepositoryProtocol
from src.domain import model
from src.domain.model import OrderLine, Batch
from src.service_layer import services


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


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch("ref", "sku", 20, None, repo, session)

    result = services.allocate("orderid", "sku", 2, repo=repo, session=session)
    assert result == "ref"


def test_error_for_invalid_sku():
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch("ref", "sku1", 20, None, repo, session)

    with pytest.raises(services.InvalidSku, match=f"Invalid sku sku"):
        services.allocate("orderid", "sku2", 2, repo=repo, session=FakeSession())


def test_commits():
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch("ref", "sku", 20, None, repo, session)
    session = FakeSession()

    services.allocate("orderid", "sku", 2, repo=repo, session=session)
    assert session.committed is True


def test_returns_deallocation():
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch("ref", "sku", 20, None, repo, session)
    result1 = services.allocate("orderid", "sku", 2, repo=repo, session=session)
    result2 = services.deallocate("orderid", "sku", 2, repo=repo, session=session)
    assert result1 == result2


######################
today = datetime.today()
tomorrow = datetime.today() + timedelta(days=1)
next_week = datetime.today() + timedelta(days=7)


def test_prefers_current_stock_batches_to_shipments():
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch("in-stock-batch", "sku", 100, None, repo, session)
    services.add_batch("shipment-batch", "sku", 100, today, repo, session)

    services.allocate("oref", "sku", 10, repo, session)
    assert repo.get("in-stock-batch").available_quantity == 90
    assert repo.get("shipment-batch").available_quantity == 100

def test_prefers_earlier_batches():
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, today, repo, session)
    services.add_batch("shipment-batch-1", "RETRO-CLOCK", 100, tomorrow, repo, session)
    services.add_batch("shipment-batch-2", "RETRO-CLOCK", 100, next_week, repo, session)
    services.allocate("oref", "RETRO-CLOCK", 10, repo, session)

    assert repo.get("in-stock-batch",).available_quantity == 90
    assert repo.get("shipment-batch-1").available_quantity == 100
    assert repo.get("shipment-batch-2").available_quantity == 100



