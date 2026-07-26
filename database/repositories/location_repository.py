from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Location
from database.repositories.base_repository import BaseRepository


LocationKey = tuple[
    str | None,
    str | None,
    str | None,
    bool,
]


class LocationRepository(BaseRepository[Location]):
    """
    Repository for Location database operations.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(session, Location)

    def find(
        self,
        city: str | None,
        state: str | None,
        country: str | None,
        remote: bool,
    ) -> Location | None:
        """
        Find one location matching all location fields.
        """

        statement = (
            select(Location)
            .where(Location.city == city)
            .where(Location.state == state)
            .where(Location.country == country)
            .where(Location.remote == remote)
        )

        return self.session.scalar(statement)

    def get_all_lookup(
        self,
    ) -> dict[LocationKey, Location]:
        """
        Fetch existing locations once and create an
        in-memory lookup dictionary.

        Key:
            (city, state, country, remote)
        """

        statement = select(Location)

        locations = self.session.scalars(statement).all()

        return {
            (
                location.city,
                location.state,
                location.country,
                location.remote,
            ): location
            for location in locations
        }