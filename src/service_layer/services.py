from sqlalchemy.orm import Session

from src.adapters.repository import RepositoryProtocol
from src.domain import model
from src.domain.model import OrderLine


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: OrderLine, repo: RepositoryProtocol, session: Session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batch_ref = model.allocate(line, batches=batches)
    session.commit()
    return batch_ref

def deallocate(line: OrderLine, repo: RepositoryProtocol, session: Session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batch_ref = model.deallocate(line, batches=batches)
    session.commit()
    return batch_ref
