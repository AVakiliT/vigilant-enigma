from alembic import context

from allocation.adapters import orm

config = context.config

target_metadata = orm.metadata