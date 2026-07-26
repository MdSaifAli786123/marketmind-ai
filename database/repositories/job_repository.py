from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Job
from database.repositories.base_repository import BaseRepository


class JobRepository(BaseRepository[Job]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, Job)

    def get_by_source_url(
        self,
        source_url: str,
    ) -> Job | None:
        statement = select(Job).where(
            Job.source_url == source_url
        )

        return self.session.scalar(statement)

    def exists_by_source_url(
        self,
        source_url: str,
    ) -> bool:
        statement = (
            select(Job.id)
            .where(Job.source_url == source_url)
            .limit(1)
        )

        return self.session.scalar(statement) is not None

    def get_existing_source_urls(
        self,
        source_urls: set[str],
    ) -> set[str]:
        if not source_urls:
            return set()

        statement = select(Job.source_url).where(
            Job.source_url.in_(source_urls)
        )

        return set(
            self.session.scalars(statement).all()
        )