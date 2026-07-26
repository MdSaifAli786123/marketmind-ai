from __future__ import annotations

from collectors.base import BaseCollector
from domain.job import Job


class WeWorkRemotelyCollector(BaseCollector):

    @property
    def source_name(self) -> str:
        return "WeWorkRemotely"

    def collect(self) -> list[Job]:
        return []