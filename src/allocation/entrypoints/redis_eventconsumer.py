import json
import logging

import redis

from allocation import config
from allocation.adapters import orm
from allocation.domain import commands
from allocation.service_layer import messagebus, unit_of_work

r = redis.Redis(**config.get_redis_host_and_port())


def handle_change_batch_quantity(m):
    logging.debug(f'handling {m}')
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(
        ref=data['batchref'],
        qty=data['qty']
    )
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity')

    for m in pubsub.listen():
        handle_change_batch_quantity(m)


if __name__ == "__main__":
    main()
