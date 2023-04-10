from datetime import date
from typing import Optional

from src.domain import model
from src.domain.model import OrderLine
from src.service_layer.unit_of_work import UnitOfWorkProtocol


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
        ref: str, sku: str, qty: int, eta: Optional[date],
        uow: UnitOfWorkProtocol
):
    with uow:
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(orderid: str, sku: str, qty: int, uow: UnitOfWorkProtocol) -> str:
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(sku, batches):
            raise InvalidSku(f"Invalid sku {sku}")
        batch_ref = model.allocate(line=OrderLine(orderid, sku, qty), batches=batches)
        uow.commit()
    return batch_ref


def deallocate(orderid: str, sku: str, qty: int, uow: UnitOfWorkProtocol) -> str:
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(sku, batches):
            raise InvalidSku(f"Invalid sku {sku}")
        batch_ref = model.deallocate(OrderLine(orderid, sku, qty), batches=batches)
        uow.commit()
    return batch_ref
