from typing import Protocol, Set

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from src.adapters import repository
from src.domain import model
from src.service_layer import messagebus

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
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY) -> None:
        self.session_factory = session_factory

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlProductRepository(

                self.session
            )

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
