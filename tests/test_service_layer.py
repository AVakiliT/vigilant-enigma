from typing import List, Set

import pytest

from src.adapters.repository import RepositoryProtocol
from src.domain import model
from src.domain.model import OrderLine, Batch
from src.service_layer import services


class FakeRepository(RepositoryProtocol):

    def __init__(self, batches: List[Batch]) -> None:
        super().__init__()
        self._batches = set(batches)

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
    line = OrderLine("orderid", "sku", 2)
    batch = Batch("ref", "sku", 20, None)
    repo = FakeRepository([batch])

    result = services.allocate(line=line, repo=repo, session=FakeSession())
    assert result == "ref"


def test_error_for_invalid_sku():
    line = OrderLine("orderid", "sku1", 2)
    batch = Batch("ref", "sku2", 20, None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match=f"Invalid sku {line.sku}"):
        services.allocate(line=line, repo=repo, session=FakeSession())



def test_commits():
    line = OrderLine("orderid", "sku", 2)
    batch = Batch("ref", "sku", 20, None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line=line, repo=repo, session=session)
    assert session.committed is True

def test_returns_deallocation():
    line = OrderLine("orderid", "sku", 2)
    batch = Batch("ref", "sku", 20, None)
    batch._allocations.add(line)
    repo = FakeRepository([batch])

    result = services.deallocate(line, repo, FakeSession())
    assert result == "ref"

