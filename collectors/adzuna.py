from __future__ import annotations

from collectors.base import BaseCollector
from domain.job import Job


class AdzunaCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "Adzuna"

    def collect(self) -> list[Job]:
        return []