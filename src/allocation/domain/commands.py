from pydantic.dataclasses import dataclass
from datetime import date


class Command:
    pass


@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: date | None


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class DeAllocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int
