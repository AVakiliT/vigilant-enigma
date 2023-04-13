from datetime import datetime, timedelta

from src.domain.model import *

today = datetime.today()
tomorrow = datetime.today() + timedelta(days=1)
next_week = datetime.today() + timedelta(days=7)


def make_batch_and_line(sku, batch_qty, line_qty):
    batch = Batch(reference="batch-001", sku=sku, qty=batch_qty, eta=date.today())
    line = OrderLine(orderid='order-ref', sku=sku, qty=line_qty)
    return batch, line


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    batch, line = make_batch_and_line("SMALL-TABLE", 1, 2)
    assert batch.can_allocate(line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line("SMALL-TABLE", 2, 2)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch(reference="batch-001", sku="SMALL-TABLE", qty=20, eta=date.today())
    line = OrderLine(orderid='order-ref', sku="BIG-TABLE", qty=2)
    assert batch.can_allocate(line) is False


def test_allocation_is_idempotent():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18

def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=today)
    line = OrderLine("oref", "RETRO-CLOCK", 10)
    product = Product("RETRO-CLOCK", [in_stock_batch, shipment_batch])
    batch_ref = product.allocate(line)
    assert batch_ref == "in-stock-batch"


