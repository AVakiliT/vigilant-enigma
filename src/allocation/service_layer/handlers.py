import allocation.domain.commands
from allocation.adapters import redis_eventpublisher
from allocation.domain import model, events
from allocation.domain.model import OrderLine
from allocation.service_layer.unit_of_work import UnitOfWorkProtocol


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
        event: allocation.domain.commands.CreateBatch,
        uow: UnitOfWorkProtocol
):
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()


def allocate(event: allocation.domain.commands.Allocate, uow: UnitOfWorkProtocol) -> str:
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {event.sku}")
        batch_ref = product.allocate(line=OrderLine(event.orderid, event.sku, event.qty))
        uow.commit()
    return batch_ref


def deallocate(event: allocation.domain.commands.DeAllocate, uow: UnitOfWorkProtocol) -> str:
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {event.sku}")
        batch_ref = product.deallocate(OrderLine(event.orderid, event.sku, event.qty))
        uow.commit()
    return batch_ref


def send_out_of_stock_notification(event: events.OutOfStock, _: UnitOfWorkProtocol):
    print(f"Out of Stock {event.sku}")


def change_batch_quantity(
       event: allocation.domain.commands.ChangeBatchQuantity, uow: UnitOfWorkProtocol
):
    with uow:
        product = uow.products.get_by_batchref(event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()


def publish_allocated_event(event: events.Allocated, _: UnitOfWorkProtocol):
    redis_eventpublisher.publish('line_allocated', event)