from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Skill
from database.repositories.base_repository import BaseRepository


class SkillRepository(BaseRepository[Skill]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, Skill)

    def get_by_name(
        self,
        name: str,
    ) -> Skill | None:
        statement = select(Skill).where(
            Skill.name == name
        )

        return self.session.scalar(statement)

    def get_by_names(
        self,
        names: set[str],
    ) -> dict[str, Skill]:
        if not names:
            return {}

        statement = select(Skill).where(
            Skill.name.in_(names)
        )

        skills = self.session.scalars(statement).all()

        return {
            skill.name: skill
            for skill in skills
        }