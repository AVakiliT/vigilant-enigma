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
        product = uow.products.get(sku)
        if product is None:
            product = model.Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(orderid: str, sku: str, qty: int, uow: UnitOfWorkProtocol) -> str:
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")
        batch_ref = product.allocate(line=OrderLine(orderid, sku, qty))
        uow.commit()
    return batch_ref


def deallocate(orderid: str, sku: str, qty: int, uow: UnitOfWorkProtocol) -> str:
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")
        batch_ref = product.deallocate(OrderLine(orderid, sku, qty))
        uow.commit()
    return batch_ref
