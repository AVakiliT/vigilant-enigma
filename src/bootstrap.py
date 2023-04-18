import inspect
from typing import Callable

import allocation.service_layer.handlers
from allocation.adapters import redis_eventpublisher, orm
from allocation.adapters.notifications import AbstractNotifications, EmailNotifications
from allocation.service_layer import unit_of_work, messagebus


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items() if name in params
    }
    return lambda message: handler(message, ** deps)


def bootstrap(
        start_orm=True,
        uow: unit_of_work.UnitOfWorkProtocol = unit_of_work.SqlAlchemyUnitOfWork(),
        notifications: AbstractNotifications = EmailNotifications(),
        publish: Callable = redis_eventpublisher.publish,
):
    if start_orm:
        orm.start_mappers()
    dependencies = dict(
        uow=uow,
        publish=publish,
        notifications=notifications
    )
    injected_event_handlers = {
        event_type: [inject_dependencies(handler, dependencies) for handler in event_handlers]
        for event_type, event_handlers in allocation.service_layer.handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: inject_dependencies(command_handler, dependencies)
        for command_type, command_handler in allocation.service_layer.handlers.COMMAND_HANDLERS.items()
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handler=injected_command_handlers
    )
