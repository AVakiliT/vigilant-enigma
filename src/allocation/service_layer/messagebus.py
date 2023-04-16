import logging
from typing import Dict, Type, List, Callable

from tenacity import Retrying, stop_after_attempt, wait_exponential, RetryError

import allocation.domain.commands
from allocation.domain import events, commands
from allocation.service_layer import handlers, unit_of_work

logger = logging.getLogger(__name__)
Message = commands.Command | events.Event

COMMAND_HANDLERS: Dict[Type[commands.Command], Callable] = {
    allocation.domain.commands.CreateBatch: handlers.add_batch,
    allocation.domain.commands.Allocate: handlers.allocate,
    allocation.domain.commands.ChangeBatchQuantity: handlers.change_batch_quantity
}

EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.Allocated: [handlers.publish_allocated_event]
}


def handle_event(event: events.Event, queue: List[Message], uow: unit_of_work.UnitOfWorkProtocol):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential()
                ):
                    with attempt:
                        logger.debug('handling event %s with handler %s', event, handler)
                        handler(event, uow=uow)
                        queue.extend(uow.collect_new_events())
            except RetryError as retry_failure:
                logger.error('Failed to handle event %s times, giving up!',retry_failure.last_attempt.attempt_number)
        except Exception:
            logger.exception('Exception handling event %s', event)
            continue


def handle_command(
        command: commands.Command,
        queue: List[Message],
        uow: unit_of_work.UnitOfWorkProtocol,
):
    logger.debug("handling command %s", command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception("Exception handling command %s", command)
        raise


def handle(message: Message, uow: unit_of_work.UnitOfWorkProtocol):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        match message:
            case events.Event():
                handle_event(message, queue, uow)
            case commands.Command():
                result = handle_command(message, queue, uow)
                results.append(result)
    return results
