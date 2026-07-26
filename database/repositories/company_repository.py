from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Company
from database.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, Company)

    def get_by_name(
        self,
        name: str,
    ) -> Company | None:
        statement = select(Company).where(
            Company.name == name
        )

        return self.session.scalar(statement)

    def get_by_names(
        self,
        names: set[str],
    ) -> dict[str, Company]:
        if not names:
            return {}

        statement = select(Company).where(
            Company.name.in_(names)
        )

        companies = self.session.scalars(statement).all()

        return {
            company.name: company
            for company in companies
        }