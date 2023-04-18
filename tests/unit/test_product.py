from datetime import datetime, timedelta

from allocation.domain import commands, events
from allocation.domain.model import Batch, Product, OrderLine
from test_handlers import bootstrap_test_app

today = datetime.today()
tomorrow = datetime.today() + timedelta(days=1)
next_week = datetime.today() + timedelta(days=7)


def test_prefers_current_stock_batches_to_shipments():
    messagebus = bootstrap_test_app()
    messagebus.handle(commands.CreateBatch("in-stock-batch", "sku", 100, None, ))
    messagebus.handle(commands.CreateBatch("shipment-batch", "sku", 100, today, ))

    messagebus.handle(commands.Allocate("oref", "sku", 10, ))
    product = messagebus.uow.products.get("sku")
    assert product.batches[0].available_quantity == 90
    assert product.batches[1].available_quantity == 100


def test_prefers_earlier_batches():
    messagebus = bootstrap_test_app()
    messagebus.handle(commands.CreateBatch("in-stock-batch", "RETRO-CLOCK", 100, today, ))
    messagebus.handle(commands.CreateBatch("shipment-batch-1", "RETRO-CLOCK", 100, tomorrow, ))
    messagebus.handle(commands.CreateBatch("shipment-batch-2", "RETRO-CLOCK", 100, next_week, ))
    messagebus.handle(commands.Allocate("oref", "RETRO-CLOCK", 10, ))

    product = messagebus.uow.products.get("RETRO-CLOCK")

    assert product.batches[0].available_quantity == 90
    assert product.batches[1].available_quantity == 100
    assert product.batches[2].available_quantity == 100


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
    product = Product(sku="SMALL-FORK", batches=[batch])
    product.allocate(OrderLine("order1", "SMALL-FORK", 10))

    allocation = product.allocate(OrderLine("order2", "SMALL-FORK", 1))
    assert product.events[-1] == events.OutOfStock(sku="SMALL-FORK")
    assert allocation is None


def test_increments_version_number():
    messagebus = bootstrap_test_app()
    messagebus.handle(commands.CreateBatch("batch_ref_1", "sku_1", 10, None))
    messagebus.handle(commands.Allocate("order_id_1", "sku_1", 1))
    assert messagebus.uow.products.get("sku_1").version_number == 1
