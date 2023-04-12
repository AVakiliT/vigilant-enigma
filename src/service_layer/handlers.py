from src.domain import model, events
from src.domain.model import OrderLine
from src.service_layer.unit_of_work import UnitOfWorkProtocol


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
        event: events.BatchCreated,
        uow: UnitOfWorkProtocol
):
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()


def allocate(event: events.AllocationRequired, uow: UnitOfWorkProtocol) -> str:
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {event.sku}")
        batch_ref = product.allocate(line=OrderLine(event.orderid, event.sku, event.qty))
        uow.commit()
    return batch_ref


def deallocate(event: events.DeAllocationRequired, uow: UnitOfWorkProtocol) -> str:
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
       event: events.BatchQuantityChanged, uow: UnitOfWorkProtocol
):
    with uow:
        product = uow.products.get_by_batchref(event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()
