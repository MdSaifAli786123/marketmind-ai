from __future__ import annotations

from collectors.base import BaseCollector
from config.settings import settings
from domain.raw_job import RawJob
from utils.http import create_session
from utils.logger import logger


class RemoteOKCollector(BaseCollector):

    API_URL = "https://remoteok.com/api"

    def __init__(self) -> None:
        self.session = create_session()

    @property
    def source_name(self) -> str:
        return "RemoteOK"

    def collect(self) -> list[RawJob]:

        logger.info(
            "Downloading jobs from RemoteOK..."
        )

        try:

            response = self.session.get(
                self.API_URL,
                timeout=settings.request_timeout,
            )

            response.raise_for_status()

            jobs = response.json()

            if jobs and "legal" in jobs[0]:
                jobs = jobs[1:]

            logger.info(
                f"Downloaded {len(jobs)} jobs."
            )

            return [
                RawJob(
                    source=self.source_name,
                    payload=job,
                )
                for job in jobs
            ]

        except Exception:

            logger.exception(
                "RemoteOK collection failed."
            )

            return []