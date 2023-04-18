import logging
from typing import Dict, Type, List, Callable

from tenacity import Retrying, stop_after_attempt, wait_exponential, RetryError

from allocation.domain import events, commands
from allocation.service_layer import unit_of_work
from allocation.service_layer.handlers import COMMAND_HANDLERS, EVENT_HANDLERS

logger = logging.getLogger(__name__)
Message = commands.Command | events.Event


class MessageBus:
    def __init__(self,
                 uow: unit_of_work.UnitOfWorkProtocol,
                 event_handlers=Dict[Type[events.Event], List[Callable]],
                 command_handler=Dict[Type[commands.Command], Callable]):
        self.queue = None
        self.command_handler = command_handler
        self.event_handlers = event_handlers
        self.uow = uow

    def handle(self, message: Message) -> None:
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            match message:
                case events.Event():
                    self.handle_event(message)
                case commands.Command():
                    self.handle_command(message)

    def handle_event(self, event: events.Event,
                     ):
        for handler in self.event_handlers[type(event)]:
            try:
                try:
                    for attempt in Retrying(
                            stop=stop_after_attempt(3),
                            wait=wait_exponential()
                    ):
                        with attempt:
                            logger.debug('handling event %s with handler %s', event, handler)
                            handler(event)
                            self.queue.extend(self.uow.collect_new_events())
                except RetryError as retry_failure:
                    logger.error('Failed to handle event %s times, giving up!',
                                 retry_failure.last_attempt.attempt_number)
            except Exception:
                logger.exception('Exception handling event %s', event)
                continue

    def handle_command(
            self,
            command: commands.Command,
    ):
        logger.debug("handling command %s", command)
        try:
            handler = self.command_handler[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise
