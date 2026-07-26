from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.connection import Base


# ==========================================================
# Association Table
# ==========================================================

job_skills = Table(
    "job_skills",
    Base.metadata,
    Column(
        "job_id",
        ForeignKey("jobs.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "skill_id",
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ==========================================================
# Company
# ==========================================================

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    jobs: Mapped[list["Job"]] = relationship(
        back_populates="company",
        cascade="all, save-update",
    )


# ==========================================================
# Location
# ==========================================================

class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    remote: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    jobs: Mapped[list["Job"]] = relationship(
        back_populates="location",
        cascade="all, save-update",
    )


# ==========================================================
# Skill
# ==========================================================

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    jobs: Mapped[list["Job"]] = relationship(
        secondary=job_skills,
        back_populates="skills",
    )


# ==========================================================
# Job
# ==========================================================

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_url: Mapped[str] = mapped_column(
        String(1000),
        unique=True,
        nullable=False,
    )

    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    salary: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    experience_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # ======================================================
    # Intelligence / Enrichment
    # ======================================================

    job_family: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    enrichment_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    enriched_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # ======================================================
    # Foreign Keys
    # ======================================================

    company_id: Mapped[int] = mapped_column(
        ForeignKey(
            "companies.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey(
            "locations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # ======================================================
    # Relationships
    # ======================================================

    company: Mapped["Company"] = relationship(
        back_populates="jobs",
    )

    location: Mapped["Location"] = relationship(
        back_populates="jobs",
    )

    skills: Mapped[list["Skill"]] = relationship(
        secondary=job_skills,
        back_populates="jobs",
    )


# ==========================================================
# Query History
# ==========================================================

class QueryHistory(Base):
    __tablename__ = "query_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    generated_sql: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )


# ==========================================================
# Pipeline Runs
# ==========================================================

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    jobs_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )