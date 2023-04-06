from datetime import date
from typing import Optional

from src.adapters.repository import RepositoryProtocol
from src.domain import model
from src.domain.model import OrderLine


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(
        ref: str, sku: str, qty: int, eta: Optional[date],
        repo: RepositoryProtocol, session
):
    repo.add(model.Batch(ref, sku, qty, eta))
    session.commit()


def allocate(orderid: str, sku: str, qty: int, repo: RepositoryProtocol, session) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")
    batch_ref = model.allocate(line=OrderLine(orderid, sku, qty), batches=batches)
    session.commit()
    return batch_ref


def deallocate(orderid: str, sku: str, qty: int, repo: RepositoryProtocol, session) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")
    batch_ref = model.deallocate(OrderLine(orderid, sku, qty), batches=batches)
    session.commit()
    return batch_ref
