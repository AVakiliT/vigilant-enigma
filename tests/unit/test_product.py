from datetime import datetime, timedelta

from src.domain import events
from src.service_layer import services
from tests.unit.test_service_layer import FakeUnitOfWork

today = datetime.today()
tomorrow = datetime.today() + timedelta(days=1)
next_week = datetime.today() + timedelta(days=7)


def test_prefers_current_stock_batches_to_shipments():
    uow = FakeUnitOfWork()
    services.add_batch("in-stock-batch", "sku", 100, None, uow)
    services.add_batch("shipment-batch", "sku", 100, today, uow)

    services.allocate("oref", "sku", 10, uow)
    product = uow.products.get("sku")
    assert product.batches[0].available_quantity == 90
    assert product.batches[1].available_quantity == 100


def test_prefers_earlier_batches():
    uow = FakeUnitOfWork()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, today, uow)
    services.add_batch("shipment-batch-1", "RETRO-CLOCK", 100, tomorrow, uow)
    services.add_batch("shipment-batch-2", "RETRO-CLOCK", 100, next_week, uow)
    services.allocate("oref", "RETRO-CLOCK", 10, uow)

    product = uow.products.get("RETRO-CLOCK")

    assert product.batches[0].available_quantity == 90
    assert product.batches[1].available_quantity == 100
    assert product.batches[2].available_quantity == 100


def test_raises_out_of_stock_exception_if_cannot_allocate():
    uow = FakeUnitOfWork()
    services.add_batch("batch_ref_1", "sku_1", 10, None, uow)
    allocation = services.allocate("order_id_1", "sku_1", 20, uow)
    product = uow.products.get("sku_1")
    assert product.events[-1] == events.OutOfStock(sku="sku_1")
    assert allocation is None


def test_increments_version_number():
    uow = FakeUnitOfWork()
    services.add_batch("batch_ref_1", "sku_1", 10, None, uow)
    services.allocate("order_id_1", "sku_1", 1, uow)
    assert uow.products.get("sku_1").version_number == 1
