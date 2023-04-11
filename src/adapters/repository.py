from typing import Protocol, Iterable, List

from sqlalchemy.orm import Session

from src.domain import model


class ProductRepositoryProtocol(Protocol):
    def add(self, product: model.Product):
        pass

    def get(self, sku: str) -> model.Product:
        pass


class SqlProductRepository(ProductRepositoryProtocol):
    def __init__(self, session: Session):
        self.session = session

    def add(self, product):
        self.session.add(product)

    def get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()
