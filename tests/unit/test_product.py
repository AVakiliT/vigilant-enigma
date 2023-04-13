from datetime import datetime, timedelta

from src.domain import events
from src.service_layer import messagebus
from tests.unit.test_handlers import FakeUnitOfWork

today = datetime.today()
tomorrow = datetime.today() + timedelta(days=1)
next_week = datetime.today() + timedelta(days=7)


def test_prefers_current_stock_batches_to_shipments():
    uow = FakeUnitOfWork()
    messagebus.handle(events.BatchCreated("in-stock-batch", "sku", 100, None,), uow)
    messagebus.handle(events.BatchCreated("shipment-batch", "sku", 100, today,), uow)

    messagebus.handle(events.AllocationRequired("oref", "sku", 10,), uow)
    product = uow.products.get("sku")
    assert product.batches[0].available_quantity == 90
    assert product.batches[1].available_quantity == 100


def test_prefers_earlier_batches():
    uow = FakeUnitOfWork()
    messagebus.handle(events.BatchCreated("in-stock-batch", "RETRO-CLOCK", 100, today,), uow)
    messagebus.handle(events.BatchCreated("shipment-batch-1", "RETRO-CLOCK", 100, tomorrow,), uow)
    messagebus.handle(events.BatchCreated("shipment-batch-2", "RETRO-CLOCK", 100, next_week,), uow)
    messagebus.handle(events.AllocationRequired("oref", "RETRO-CLOCK", 10,), uow)

    product = uow.products.get("RETRO-CLOCK")

    assert product.batches[0].available_quantity == 90
    assert product.batches[1].available_quantity == 100
    assert product.batches[2].available_quantity == 100


def test_raises_out_of_stock_exception_if_cannot_allocate():
    uow = FakeUnitOfWork()
    messagebus.handle(events.BatchCreated("batch_ref_1", "sku_1", 10, None), uow)
    allocation =messagebus.handle(events.AllocationRequired("order_id_1", "sku_1", 20), uow)[0]
    # product = uow.products.get("sku_1")
    # assert product.events[-1] == events.OutOfStock(sku="sku_1")
    assert allocation is None


def test_increments_version_number():
    uow = FakeUnitOfWork()
    messagebus.handle(events.BatchCreated("batch_ref_1", "sku_1", 10, None), uow)
    messagebus.handle(events.AllocationRequired("order_id_1", "sku_1", 1), uow)
    assert uow.products.get("sku_1").version_number == 1
