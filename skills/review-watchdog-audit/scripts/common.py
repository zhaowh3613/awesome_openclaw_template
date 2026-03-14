"""Shared utilities for review-watchdog-audit scripts."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OPENCLAW_DIR = Path(os.environ.get("OPENCLAW_DIR", Path.home() / ".openclaw"))


def now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def now_stamp() -> str:
    """Return current UTC time as a compact timestamp string."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def safe_read_json(path: Path) -> Any:
    """Read and parse a JSON file, returning *None* on any error."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def extract_job_name(job: dict[str, Any], idx: int) -> str:
    """Extract a human-readable name from a job dict."""
    for key in ("id", "name", "jobId", "label"):
        val = job.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return f"job-{idx}"


def extract_jobs(payload: Any) -> tuple[list[dict[str, Any]], str]:
    """Return (jobs_list, schema_type) from a jobs payload.

    *schema_type* is ``"dict"`` when the payload wraps jobs in
    ``{"jobs": [...]}`` or ``"list"`` when the payload is the list itself.
    """
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload["jobs"], "dict"
    if isinstance(payload, list):
        return payload, "list"
    raise ValueError("Unsupported jobs schema")


def save_jobs(path: Path, original: Any, jobs: list[dict[str, Any]], schema: str) -> None:
    """Write *jobs* back to *path*, preserving the original schema shape."""
    if schema == "dict":
        original["jobs"] = jobs
        content = original
    else:
        content = jobs
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
