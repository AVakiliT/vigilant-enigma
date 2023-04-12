import abc
from typing import Protocol, Iterable, List, Set

from sqlalchemy.orm import Session

from src.domain import model


class AbstractRepository(abc.ABC):
    def __init__(self):
        self.seen = set()  # type: Set[model.Product]

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    def _add(self, product: model.Product):
        ...

    def _get(self, sku) -> model.Product:
        ...


class SqlProductRepository(AbstractRepository):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()


# class TrackingRepository(ProductRepositoryProtocol):
#     seen: Set[model.Product]
#
#     def __init__(self, repo: ProductRepositoryProtocol):
#         self._repo = repo
#         self.seen = set()
#
#     def add(self, product: model.Product):
#         self._repo.add(product)
#         self.seen.add(product)
#
#     def get(self, sku: str) -> model.Product:
#         product = self._repo.get(sku)
#         if product:
#             self.seen.add(product)
#         return product
