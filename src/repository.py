from typing import Protocol

from sqlalchemy.orm import Session

from src import model


class RepositoryProtocol(Protocol):
    def add(self, batch: model.Batch):
        pass

    def get(self, reference: str) -> model.Batch:
        pass


class SqlRepository(RepositoryProtocol):
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)
        # self.session.commit()

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()