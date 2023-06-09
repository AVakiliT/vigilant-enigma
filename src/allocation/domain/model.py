from dataclasses import dataclass
from datetime import date
from typing import Optional, List

from allocation.domain import events, commands


class NotAllocated(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(
            self, reference: str, sku: str, qty: int, eta: Optional[date]) -> None:
        self.eta = eta
        self._purchased_quantity = qty
        self.sku = sku
        self.reference = reference
        self._allocations = set()

    def allocate(self, line):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line):
        self._allocations.discard(line)

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    def can_allocate(self, line: OrderLine):
        return self.sku == line.sku and self.available_quantity >= line.qty

    def is_allocated_to(self, line: OrderLine):
        return line in self._allocations

    @property
    def available_quantity(self):
        return self._purchased_quantity - self.allocated_quantity

    @property
    def allocated_quantity(self):
        return sum(a.qty for a in self._allocations)

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __le__(self, other):
        if self.eta is None:
            return True
        if other.eta is None:
            return False
        return self.eta < other.eta

    def __repr__(self):
        return f"<Batch {self.reference}>"


class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number=0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events: List[events.Event | commands.Command] = []

    def allocate(self, line: OrderLine) -> str | None:
        try:
            batch = next(batch for batch in sorted(self.batches) if batch.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            self.events.append(events.Allocated(
                orderid=line.orderid, sku=line.sku, qty=line.qty, batchref=batch.reference
            ))
            return batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            return None

    def deallocate(self, line: OrderLine) -> str:
        try:
            batch = next(batch for batch in self.batches if batch.is_allocated_to(line))
            batch.deallocate(line)
            return batch.reference
        except StopIteration:
            raise NotAllocated(f"Not allocated to any batch")

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(
                commands.Allocate(line.orderid, line.sku, line.qty)
            )
