from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from config.settings import PROJECT_ROOT
from utils.logger import logger


# ==========================================================
# Configuration
# ==========================================================

STATE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "runtime"
)

STATE_FILE = (
    STATE_DIRECTORY
    / "refresh_state.json"
)

STATE_VERSION = "refresh-state-v1"


# ==========================================================
# Helpers
# ==========================================================

def _utc_now_iso() -> str:
    """
    Return the current UTC timestamp in ISO-8601 format.
    """

    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


def _json_default(
    value: Any,
) -> str:
    """
    Convert objects such as datetime and Path into
    JSON-compatible string representations.
    """

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        Path,
    ):
        return str(value)

    raise TypeError(
        f"Object of type "
        f"{type(value).__name__} "
        f"is not JSON serializable."
    )


# ==========================================================
# Default State
# ==========================================================

def default_refresh_state(
) -> dict[str, Any]:
    """
    State returned when no refresh has been recorded yet.
    """

    return {
        "state_version": (
            STATE_VERSION
        ),

        "has_refresh_history": False,

        "status": "never_run",

        "success": False,

        "started_at": None,

        "completed_at": None,

        "duration_seconds": None,

        "ingestion": {},

        "enrichment_count": 0,

        "enrichment_failed": 0,

        "vector_sync": {},

        "error": None,

        "saved_at": None,
    }


# ==========================================================
# Save State
# ==========================================================

def save_refresh_state(
    result: Any,
) -> dict[str, Any]:
    """
    Persist the latest refresh result.

    The write uses a temporary file followed by replacement,
    reducing the chance of leaving a partially written JSON
    state file if writing fails.
    """

    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


    # ------------------------------------------------------
    # Convert RefreshResult to dictionary
    # ------------------------------------------------------

    if hasattr(
        result,
        "to_dict",
    ):

        raw_state = (
            result.to_dict()
        )

    elif isinstance(
        result,
        dict,
    ):

        raw_state = dict(
            result
        )

    else:

        raise TypeError(
            "Refresh state must be a dictionary "
            "or expose to_dict()."
        )


    # ------------------------------------------------------
    # Add State Metadata
    # ------------------------------------------------------

    state: dict[
        str,
        Any,
    ] = {
        "state_version": (
            STATE_VERSION
        ),

        "has_refresh_history": True,

        **raw_state,

        "saved_at": (
            _utc_now_iso()
        ),
    }


    # ------------------------------------------------------
    # Serialize first
    # ------------------------------------------------------

    serialized = json.dumps(
        state,
        indent=2,
        ensure_ascii=False,
        default=_json_default,
    )


    # ------------------------------------------------------
    # Atomic Write
    # ------------------------------------------------------

    temporary_path: Path | None = None

    try:

        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=STATE_DIRECTORY,
            prefix="refresh_state_",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:

            temporary_file.write(
                serialized
            )

            temporary_file.flush()

            temporary_path = Path(
                temporary_file.name
            )


        temporary_path.replace(
            STATE_FILE
        )


    except Exception:

        if (
            temporary_path is not None
            and temporary_path.exists()
        ):

            try:

                temporary_path.unlink()

            except OSError:

                pass

        logger.exception(
            "Failed to persist refresh state."
        )

        raise


    logger.info(
        "Refresh state saved: "
        f"{STATE_FILE}"
    )

    return state


# ==========================================================
# Load State
# ==========================================================

def load_refresh_state(
) -> dict[str, Any]:
    """
    Load the latest persisted refresh state.

    If the state has never been created, return the default
    never-run state.
    """

    if not STATE_FILE.exists():

        return (
            default_refresh_state()
        )


    try:

        with STATE_FILE.open(
            mode="r",
            encoding="utf-8",
        ) as file:

            state = json.load(
                file
            )


        if not isinstance(
            state,
            dict,
        ):

            raise ValueError(
                "Refresh state must contain "
                "a JSON object."
            )


        return state


    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ):

        logger.exception(
            "Unable to load persisted "
            "refresh state."
        )

        state = (
            default_refresh_state()
        )

        state["status"] = (
            "state_unavailable"
        )

        state["error"] = (
            "Persisted refresh state "
            "could not be loaded."
        )

        return state


# ==========================================================
# Clear State
# ==========================================================

def clear_refresh_state(
) -> bool:
    """
    Delete persisted refresh history.

    Mainly useful during local development.
    """

    if not STATE_FILE.exists():
        return False

    STATE_FILE.unlink()

    logger.info(
        "Refresh state cleared."
    )

    return True


# ==========================================================
# Convenience Status
# ==========================================================

def get_refresh_status(
) -> dict[str, Any]:
    """
    Return the latest persisted refresh state.
    """

    return load_refresh_state()


# ==========================================================
# Manual Inspection
# ==========================================================

if __name__ == "__main__":

    state = (
        load_refresh_state()
    )

    print(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False,
            default=_json_default,
        )
    )