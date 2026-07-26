from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RawJob:
    """
    Raw job collected from an external source.
    """

    source: str
    payload: dict[str, Any]