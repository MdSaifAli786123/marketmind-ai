from __future__ import annotations

from abc import ABC, abstractmethod

from domain.job import Job
from domain.raw_job import RawJob


class BaseTransformer(ABC):
    """
    Base class for transforming RawJob objects into Job objects.
    """

    @abstractmethod
    def transform(self, raw_job: RawJob) -> Job:
        """
        Transform one RawJob into one validated Job.
        """
        ...