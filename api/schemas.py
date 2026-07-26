from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website: str | None = None


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    city: str | None = None
    state: str | None = None
    country: str | None = None
    remote: bool


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str

    company: CompanyResponse
    location: LocationResponse
    skills: list[SkillResponse]

    source: str
    source_url: str

    posted_at: datetime | None = None
    salary: str | None = None

    job_type: str
    experience_level: str
    job_family: str | None = None

    enrichment_version: str | None = None
    enriched_at: datetime | None = None

    created_at: datetime


class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str

    company: CompanyResponse
    location: LocationResponse
    skills: list[SkillResponse]

    source: str
    source_url: str

    posted_at: datetime | None = None
    salary: str | None = None

    job_type: str
    experience_level: str
    job_family: str | None = None


class PaginatedJobsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

    jobs: list[JobSummaryResponse]