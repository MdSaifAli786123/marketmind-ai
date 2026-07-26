from pydantic import BaseModel


class Location(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None
    remote: bool = False