from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field

from domain.company import Company
from domain.enums import ExperienceLevel, JobType
from domain.location import Location


class Job(BaseModel):
    title: str

    company: Company

    location: Location

    description: str

    source: str

    source_url: HttpUrl

    posted_at: datetime | None = None

    salary: str | None = None

    job_type: JobType = JobType.UNKNOWN

    experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN

    skills: list[str] = Field(default_factory=list)