from __future__ import annotations

from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.repositories.company_repository import CompanyRepository
from database.repositories.job_repository import JobRepository
from database.repositories.location_repository import LocationRepository
from database.repositories.skill_repository import SkillRepository


class UnitOfWork:
    """
    Coordinates repositories within one database transaction.
    """

    def __init__(self) -> None:
        self.session: Session | None = None

        self.companies: CompanyRepository
        self.locations: LocationRepository
        self.skills: SkillRepository
        self.jobs: JobRepository

    def __enter__(self) -> "UnitOfWork":
        self.session = SessionLocal()

        self.companies = CompanyRepository(self.session)
        self.locations = LocationRepository(self.session)
        self.skills = SkillRepository(self.session)
        self.jobs = JobRepository(self.session)

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if self.session is None:
            return

        try:
            if exc_type is not None:
                self.session.rollback()
        finally:
            self.session.close()
            self.session = None

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not active.")

        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not active.")

        self.session.rollback()

    def flush(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not active.")

        self.session.flush()