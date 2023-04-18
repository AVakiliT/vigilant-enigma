import json
import logging

import redis

import bootstrap
from allocation import config
from allocation.adapters import orm
from allocation.domain import commands

r = redis.Redis(**config.get_redis_host_and_port())


def handle_change_batch_quantity(m, bus):
    logging.debug(f'handling {m}')
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(
        ref=data['batchref'],
        qty=data['qty']
    )
    bus.handle(cmd)


def main():
    bus = bootstrap.bootstrap()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity')

    for m in pubsub.listen():
        handle_change_batch_quantity(m, bus)


if __name__ == "__main__":
    main()
