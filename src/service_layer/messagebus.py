from typing import Dict, Type, List, Callable

from src.domain import events
from src.service_layer import unit_of_work, handlers


def handle(event: events.Event, uow: unit_of_work):
    results = []
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow))
            queue.extend(uow.collect_new_events())
    return results


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.BatchCreated: [handlers.add_batch],
    events.AllocationRequired: [handlers.allocate],
    events.BatchQuantityChanged: [handlers.change_batch_quantity]
}
