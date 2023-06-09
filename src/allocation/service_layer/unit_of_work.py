from typing import Protocol

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocation import config
from allocation.adapters import repository

DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(
    config.get_postgres_uri(),
    isolation_level="REPEATABLE READ"
))


class UnitOfWorkProtocol(Protocol):
    products: repository.AbstractRepository

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def __enter__(self):
        return self

    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)

    def commit(self):
        self._commit()

    def rollback(self):
        ...

    def _commit(self):
        ...


class SqlAlchemyUnitOfWork(UnitOfWorkProtocol):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory
        super().__init__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        self.session.close()

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlProductRepository(
            self.session
        )

        return super().__enter__()

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
