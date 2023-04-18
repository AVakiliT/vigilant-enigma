from typing import Callable, Dict, Type, List

import allocation.domain
import allocation.domain.commands
from allocation.adapters import redis_eventpublisher, notifications
from allocation.domain import model, events, commands
from allocation.domain.model import OrderLine
from allocation.service_layer.unit_of_work import UnitOfWorkProtocol


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
        command: allocation.domain.commands.CreateBatch,
        uow: UnitOfWorkProtocol
):
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(command.ref, command.sku, command.qty, command.eta))
        uow.commit()


def allocate(command: allocation.domain.commands.Allocate, uow: UnitOfWorkProtocol) -> str:
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {command.sku}")
        batch_ref = product.allocate(line=OrderLine(command.orderid, command.sku, command.qty))
        uow.commit()
    return batch_ref


def deallocate(command: allocation.domain.commands.DeAllocate, uow: UnitOfWorkProtocol) -> str:
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {command.sku}")
        batch_ref = product.deallocate(OrderLine(command.orderid, command.sku, command.qty))
        uow.commit()
    return batch_ref


def send_out_of_stock_notification(event: events.OutOfStock, notifications: notifications.AbstractNotifications,):
    notifications.send(
        'stock@made.com',
        f'Out of stock for {event.sku}',
    )


def change_batch_quantity(
       event: allocation.domain.commands.ChangeBatchQuantity, uow: UnitOfWorkProtocol
):
    with uow:
        product = uow.products.get_by_batchref(event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()


def publish_allocated_event(event: events.Allocated):
    redis_eventpublisher.publish('line_allocated', event)


COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
    allocation.domain.commands.CreateBatch: add_batch,
    allocation.domain.commands.Allocate: allocate,
    allocation.domain.commands.ChangeBatchQuantity: change_batch_quantity
}
EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [send_out_of_stock_notification],
    events.Allocated: [publish_allocated_event]
}
