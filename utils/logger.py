import sys
from pathlib import Path

from loguru import logger

from config.settings import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sys.stderr,
    level=settings.log_level,
    colorize=True,
    enqueue=True,
)

logger.add(
    LOG_DIR / "application.log",
    level=settings.log_level,
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    enqueue=True,
    encoding="utf-8",
)

__all__ = ["logger"]