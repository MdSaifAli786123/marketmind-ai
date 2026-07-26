from __future__ import annotations

from collectors.base import BaseCollector
from domain.raw_job import RawJob
from utils.logger import logger


class CollectorManager:

    def __init__(self, collectors: list[BaseCollector]) -> None:
        self.collectors = collectors

    def collect_all(self) -> list[RawJob]:

        all_jobs: list[RawJob] = []

        for collector in self.collectors:

            logger.info(
                f"Collecting from {collector.source_name}"
            )

            jobs = collector.collect()

            logger.info(
                f"{collector.source_name}: {len(jobs)} jobs collected."
            )

            all_jobs.extend(jobs)

        logger.info(
            f"Total raw jobs collected: {len(all_jobs)}"
        )

        return all_jobs