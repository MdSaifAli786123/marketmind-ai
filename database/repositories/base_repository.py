from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing common CRUD operations.
    """

    def __init__(
        self,
        session: Session,
        model: type[ModelType],
    ) -> None:
        self.session = session
        self.model = model

    def add(self, entity: ModelType) -> ModelType:
        """
        Add an entity to the current session.
        """
        self.session.add(entity)
        return entity

    def get_by_id(self, entity_id: int) -> ModelType | None:
        """
        Retrieve an entity by its primary key.
        """
        return self.session.get(self.model, entity_id)

    def get_all(self) -> list[ModelType]:
        """
        Return all records.
        """
        statement = select(self.model)
        return list(self.session.scalars(statement))

    def delete(self, entity: ModelType) -> None:
        """
        Delete an entity.
        """
        self.session.delete(entity)

    def flush(self) -> None:
        """
        Flush pending changes.
        """
        self.session.flush()

    def commit(self) -> None:
        """
        Commit the current transaction.
        """
        self.session.commit()

    def rollback(self) -> None:
        """
        Roll back the current transaction.
        """
        self.session.rollback()