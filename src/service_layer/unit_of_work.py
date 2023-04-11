from typing import Protocol

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from src.adapters import repository

DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(
    config.get_postgres_uri(),
    isolation_level="REPEATABLE READ"
))


class UnitOfWorkProtocol(Protocol):
    products: repository.ProductRepositoryProtocol

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def __enter__(self):
        raise NotImplementedError

    def commit(self):
        raise NotImplementedError

    def rollback(self):
        raise NotImplementedError


class SqlUnitOfWork(UnitOfWorkProtocol):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY) -> None:
        self.session_factory = session_factory

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlProductRepository(self.session)
        # return super.__enter__()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
