from datetime import datetime, timedelta
from typing import List

import pytest

from src.adapters.repository import ProductRepositoryProtocol
from src.domain import model
from src.service_layer import services
from src.service_layer.unit_of_work import UnitOfWorkProtocol


class FakeProductRepository(ProductRepositoryProtocol):

    def __init__(self, products) -> None:
        super().__init__(products)
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

class FakeUnitOfWork(UnitOfWorkProtocol):
    def __init__(self):
        self.products = FakeProductRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def __enter__(self):
        pass

def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()
    services.add_batch("batch_ref", "SKU", 100, None, uow)
    assert uow.products.get("SKU") is not None
    assert uow.committed

def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "GARISH-RUG", 100, None, uow)
    services.add_batch("b2", "GARISH-RUG", 99, None, uow)
    assert "b2" in [b.reference for b in uow.products.get("GARISH-RUG").batches]
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

