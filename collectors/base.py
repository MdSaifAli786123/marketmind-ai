from __future__ import annotations

from abc import ABC, abstractmethod

from domain.raw_job import RawJob


class BaseCollector(ABC):
    """Base interface for all collectors."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    def collect(self) -> list[RawJob]:
        """
        Return raw jobs.
        """
        ...