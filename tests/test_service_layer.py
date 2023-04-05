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
