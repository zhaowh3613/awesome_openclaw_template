#!/usr/bin/env python3
"""
Read-only cron watchdog audit.

Outputs:
- Human-readable summary to stdout
- JSON report file (default: ./review-watchdog-audit-report.json)
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_OPENCLAW_DIR,
    extract_job_name,
    now_iso,
    safe_read_json,
)

WATCH_KEYWORDS = ("review", "watch", "pr", "pull request", "github")
ERROR_402_PATTERNS = ("402", "quota", "payment required", "zenmux")
TOKEN_FIELDS = ("tokens", "token_count", "total_tokens", "usage")
CURSOR_FIELDS = ("cursor", "lastPrId", "lastUpdated", "checkpoint", "since")

# --- Thresholds ---
CONSECUTIVE_FAIL_P0 = 5
WASTE_RATIO_P0 = 0.50
WASTE_RATIO_P1 = 0.30
STALE_CURSOR_DAYS = 7
DURATION_SPIKE_FACTOR = 3.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RunRecord:
    """A single parsed execution record from a JSONL log."""
    timestamp: str | None = None
    status: str = "unknown"       # "success" / "fail"
    error_type: str | None = None  # "quota_402" / "generic" / None
    duration_ms: int | None = None
    token_usage: int | None = None


@dataclass
class JobFinding:
    name: str
    score: int
    severity: str
    reasons: list[str] = field(default_factory=list)
    schedule: str | None = None
    enabled: bool | None = None
    # enhanced fields
    consecutive_failures: int = 0
    avg_duration_ms: float | None = None
    has_backoff: bool | None = None
    total_tokens: int | None = None
    wasted_tokens: int | None = None
    waste_ratio: float | None = None
    duplicate_of: str | None = None


@dataclass
class StateAudit:
    cursor_value: Any = None
    last_updated: str | None = None
    is_stale: bool = False
    cursor_regressed: bool = False
    duplicate_prs: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def score_watch_job(job: dict[str, Any]) -> int:
    text = json.dumps(job, ensure_ascii=False).lower()
    return sum(1 for kw in WATCH_KEYWORDS if kw in text)


def _get_schedule(job: dict[str, Any]) -> str | None:
    for key in ("schedule", "cron", "interval", "every"):
        if job.get(key) is not None:
            return str(job[key])
    return None


# ---------------------------------------------------------------------------
# JSONL log parsing
# ---------------------------------------------------------------------------


def _extract_token_usage(record: dict[str, Any]) -> int | None:
    """Try to pull a token count from a structured log record."""
    for key in TOKEN_FIELDS:
        val = record.get(key)
        if isinstance(val, (int, float)) and val > 0:
            return int(val)
        # nested usage object: {"usage": {"total_tokens": 123}}
        if isinstance(val, dict):
            for sub in ("total_tokens", "total", "tokens"):
                sv = val.get(sub)
                if isinstance(sv, (int, float)) and sv > 0:
                    return int(sv)
    return None


def _parse_single_line(line: str) -> RunRecord | None:
    """Parse one JSONL line into a RunRecord (returns None on failure)."""
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        # fallback: treat as plain text
        lower = line.lower()
        status = "fail" if any(p in lower for p in ("error", "failed", "exception", "exit code")) else "success"
        error_type = "quota_402" if any(p in lower for p in ERROR_402_PATTERNS) else ("generic" if status == "fail" else None)
        return RunRecord(status=status, error_type=error_type)

    # structured record
    ts = obj.get("timestamp") or obj.get("ts") or obj.get("time")
    status_raw = str(obj.get("status", obj.get("result", ""))).lower()
    is_fail = status_raw in ("fail", "failed", "error") or any(
        p in json.dumps(obj, ensure_ascii=False).lower() for p in ("error", "failed", "exception")
    )
    status = "fail" if is_fail else "success"

    error_type = None
    if is_fail:
        text = json.dumps(obj, ensure_ascii=False).lower()
        error_type = "quota_402" if any(p in text for p in ERROR_402_PATTERNS) else "generic"

    duration = obj.get("duration_ms") or obj.get("duration") or obj.get("elapsed_ms")
    if isinstance(duration, (int, float)):
        duration = int(duration)
    else:
        duration = None

    token_usage = _extract_token_usage(obj)

    return RunRecord(
        timestamp=str(ts) if ts else None,
        status=status,
        error_type=error_type,
        duration_ms=duration,
        token_usage=token_usage,
    )


def parse_run_records(runs_dir: Path, max_files: int, grep_name: str) -> list[RunRecord]:
    """Parse JSONL run logs, returning structured records for *grep_name*."""
    if not runs_dir.exists():
        return []
    files = sorted(runs_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]
    pattern = re.compile(re.escape(grep_name), re.IGNORECASE)
    records: list[RunRecord] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not pattern.search(text):
            continue
        for line in text.splitlines():
            rec = _parse_single_line(line)
            if rec is not None:
                records.append(rec)
    return records


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------


def _consecutive_tail_failures(records: list[RunRecord]) -> int:
    """Count how many of the most-recent records are consecutive failures."""
    # sort by timestamp if available; otherwise keep original order
    sorted_recs = sorted(
        records,
        key=lambda r: r.timestamp or "",
        reverse=True,
    )
    count = 0
    for r in sorted_recs:
        if r.status == "fail":
            count += 1
        else:
            break
    return count


def _check_backoff(records: list[RunRecord]) -> bool | None:
    """Return True if there is evidence of increasing intervals after failures."""
    fail_timestamps: list[datetime] = []
    for r in records:
        if r.status == "fail" and r.timestamp:
            try:
                dt = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00"))
                fail_timestamps.append(dt)
            except (ValueError, TypeError):
                continue
    if len(fail_timestamps) < 3:
        return None  # not enough data
    fail_timestamps.sort()
    gaps = [(fail_timestamps[i + 1] - fail_timestamps[i]).total_seconds() for i in range(len(fail_timestamps) - 1)]
    # backoff present if gaps are generally increasing
    increasing = sum(1 for i in range(len(gaps) - 1) if gaps[i + 1] > gaps[i])
    return increasing > len(gaps) // 2


def _token_stats(records: list[RunRecord]) -> tuple[int | None, int | None, float | None]:
    """Return (total_tokens, wasted_tokens, waste_ratio)."""
    total = 0
    wasted = 0
    has_data = False
    for r in records:
        if r.token_usage is not None:
            has_data = True
            total += r.token_usage
            if r.status == "fail":
                wasted += r.token_usage
    if not has_data:
        return None, None, None
    ratio = wasted / total if total > 0 else 0.0
    return total, wasted, ratio


def _duration_stats(records: list[RunRecord]) -> tuple[float | None, list[str]]:
    """Return (avg_duration_ms, anomaly reasons)."""
    durations = [r.duration_ms for r in records if r.duration_ms is not None]
    if not durations:
        return None, []
    avg = sum(durations) / len(durations)
    reasons: list[str] = []
    spikes = [d for d in durations if d > avg * DURATION_SPIKE_FACTOR]
    if spikes:
        reasons.append(
            f"Duration spikes detected: {len(spikes)} runs exceeded {DURATION_SPIKE_FACTOR}x average "
            f"({avg:.0f}ms avg, max {max(durations)}ms)."
        )
    return avg, reasons


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify_job(
    job: dict[str, Any],
    name: str,
    score: int,
    records: list[RunRecord],
) -> JobFinding:
    reasons: list[str] = []
    severity = "P2"

    # --- failure counting ---
    failures = sum(1 for r in records if r.status == "fail")
    err402 = sum(1 for r in records if r.error_type == "quota_402")
    consec = _consecutive_tail_failures(records)

    # --- token stats ---
    total_tokens, wasted_tokens, waste_ratio = _token_stats(records)

    # --- duration ---
    avg_dur, dur_reasons = _duration_stats(records)
    reasons.extend(dur_reasons)

    # --- backoff ---
    has_backoff = _check_backoff(records)

    # --- severity determination ---
    if score <= 0:
        severity = "P2"
        reasons.append("No strong watch/review signals in job definition.")
    else:
        if err402 >= 3:
            severity = "P0"
            reasons.append(f"Detected repeated quota/402-like failures ({err402} matches).")
        if consec >= CONSECUTIVE_FAIL_P0:
            severity = "P0"
            reasons.append(f"Consecutive recent failures: {consec} (threshold {CONSECUTIVE_FAIL_P0}).")
        if waste_ratio is not None and waste_ratio >= WASTE_RATIO_P0:
            severity = "P0"
            reasons.append(f"Token waste ratio {waste_ratio:.0%} exceeds {WASTE_RATIO_P0:.0%} threshold.")
        if severity != "P0":
            if failures >= 3:
                severity = "P1"
                reasons.append(f"Detected repeated failures ({failures} suspicious log lines).")
            if waste_ratio is not None and waste_ratio >= WASTE_RATIO_P1:
                severity = "P1"
                reasons.append(f"Token waste ratio {waste_ratio:.0%} exceeds {WASTE_RATIO_P1:.0%} threshold.")
        if severity == "P2" and not reasons:
            reasons.append("No obvious repeat-failure pattern found in sampled logs.")

    if score > 0 and not records:
        reasons.append("No recent run logs found for this task; verify whether it is stale or inactive.")

    if has_backoff is False:
        reasons.append("No backoff detected between consecutive failures — task retries at full frequency, accelerating token burn.")

    schedule = _get_schedule(job)
    enabled = job.get("enabled") if isinstance(job.get("enabled"), bool) else None

    return JobFinding(
        name=name,
        score=score,
        severity=severity,
        reasons=reasons,
        schedule=schedule,
        enabled=enabled,
        consecutive_failures=consec,
        avg_duration_ms=avg_dur,
        has_backoff=has_backoff,
        total_tokens=total_tokens,
        wasted_tokens=wasted_tokens,
        waste_ratio=waste_ratio,
    )


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


_SCOPE_KEYS = ("repo", "repos", "org", "target", "scope", "repository", "owner")


def _extract_scope(job: dict[str, Any]) -> set[str]:
    """Extract a normalised set of scope identifiers from a job."""
    scope: set[str] = set()
    for key in _SCOPE_KEYS:
        val = job.get(key)
        if isinstance(val, str) and val.strip():
            scope.add(val.strip().lower())
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str) and item.strip():
                    scope.add(item.strip().lower())
    return scope


def detect_duplicates(
    jobs: list[dict[str, Any]],
    findings: list[JobFinding],
) -> list[tuple[str, str]]:
    """Detect duplicate watch jobs and update findings in-place.

    Returns a list of ``(duplicate_name, original_name)`` pairs.
    """
    name_scope: list[tuple[str, set[str]]] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        name = extract_job_name(job, 0)
        sc = _extract_scope(job)
        if sc:
            name_scope.append((name, sc))

    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for i, (name_a, scope_a) in enumerate(name_scope):
        if name_a in seen:
            continue
        for j in range(i + 1, len(name_scope)):
            name_b, scope_b = name_scope[j]
            if name_b in seen:
                continue
            if scope_a & scope_b:
                pairs.append((name_b, name_a))
                seen.add(name_b)
                for f in findings:
                    if f.name == name_b:
                        f.duplicate_of = name_a
                        f.reasons.append(f"Duplicate scope overlap with '{name_a}' — double token consumption.")
                        # boost severity by one level
                        if f.severity == "P2":
                            f.severity = "P1"
                        elif f.severity == "P1":
                            f.severity = "P0"
    return pairs


# ---------------------------------------------------------------------------
# State file audit
# ---------------------------------------------------------------------------


def audit_state_file(state_path: Path) -> StateAudit:
    """Inspect the watch state file for cursor issues."""
    audit = StateAudit()
    data = safe_read_json(state_path)
    if data is None or not isinstance(data, dict):
        return audit

    # extract cursor
    for key in CURSOR_FIELDS:
        if data.get(key) is not None:
            audit.cursor_value = data[key]
            break

    # last updated
    for key in ("lastUpdated", "updatedAt", "last_run", "timestamp"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            audit.last_updated = val.strip()
            break

    # stale cursor check
    if audit.last_updated:
        try:
            last_dt = datetime.fromisoformat(audit.last_updated.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - last_dt).days
            if age_days > STALE_CURSOR_DAYS:
                audit.is_stale = True
                audit.issues.append(
                    f"Cursor has not advanced for {age_days} days (threshold {STALE_CURSOR_DAYS})."
                )
        except (ValueError, TypeError):
            pass

    # cursor regression (needs history)
    history = data.get("history") or data.get("cursorHistory")
    if isinstance(history, list) and len(history) >= 2:
        prev = history[-2]
        curr = history[-1]
        if isinstance(prev, (int, float, str)) and isinstance(curr, (int, float, str)):
            if str(curr) < str(prev):
                audit.cursor_regressed = True
                audit.issues.append(
                    f"Cursor regressed from {prev} to {curr} — may cause duplicate processing."
                )

    # duplicate PR detection
    processed = data.get("processedPrs") or data.get("processed_prs") or data.get("reviewed")
    if isinstance(processed, list):
        seen: set[str] = set()
        for pr_id in processed:
            key = str(pr_id)
            if key in seen:
                audit.duplicate_prs.append(key)
            seen.add(key)
        if audit.duplicate_prs:
            audit.issues.append(
                f"Found {len(audit.duplicate_prs)} duplicate PR(s) in processed list: {audit.duplicate_prs[:5]}."
            )

    return audit


def apply_state_audit_to_findings(audit: StateAudit, findings: list[JobFinding]) -> None:
    """Merge state audit results into findings, adjusting severity."""
    if not audit.issues:
        return
    for f in findings:
        if f.score <= 0:
            continue
        f.reasons.extend(audit.issues)
        if audit.cursor_regressed and f.severity != "P0":
            f.severity = "P0"
        elif audit.is_stale and f.severity == "P2":
            f.severity = "P1"
        if audit.duplicate_prs and f.severity == "P2":
            f.severity = "P1"


# ---------------------------------------------------------------------------
# Main — entry point for CLI and importable for patrol.py
# ---------------------------------------------------------------------------


def run_audit(
    jobs_path: Path,
    runs_dir: Path,
    state_path: Path,
    max_run_files: int = 80,
) -> dict[str, Any]:
    """Core audit logic. Returns the report dict."""
    jobs_payload = safe_read_json(jobs_path)
    jobs: list[dict[str, Any]] = []
    if isinstance(jobs_payload, dict) and isinstance(jobs_payload.get("jobs"), list):
        jobs = jobs_payload["jobs"]
    elif isinstance(jobs_payload, list):
        jobs = jobs_payload

    findings: list[JobFinding] = []
    for i, job in enumerate(jobs):
        if not isinstance(job, dict):
            continue
        name = extract_job_name(job, i)
        score = score_watch_job(job)
        if score <= 0:
            continue
        records = parse_run_records(runs_dir, max_run_files, name)
        findings.append(classify_job(job, name, score, records))

    # duplicate detection
    duplicates = detect_duplicates(jobs, findings)

    # state audit
    state_audit = audit_state_file(state_path)
    apply_state_audit_to_findings(state_audit, findings)

    p0 = [f for f in findings if f.severity == "P0"]
    p1 = [f for f in findings if f.severity == "P1"]
    p2 = [f for f in findings if f.severity == "P2"]

    report: dict[str, Any] = {
        "generatedAt": now_iso(),
        "inputs": {
            "jobs": str(jobs_path),
            "runsDir": str(runs_dir),
            "stateFile": str(state_path),
        },
        "summary": {
            "watchJobsFound": len(findings),
            "P0": len(p0),
            "P1": len(p1),
            "P2": len(p2),
        },
        "findings": [asdict(f) for f in findings],
        "duplicates": [{"duplicate": d, "original": o} for d, o in duplicates],
        "stateAudit": asdict(state_audit),
        "recommendation": {
            "action": "stop-p0-first" if p0 else ("tune-p1" if p1 else "keep"),
            "note": "Run stop_cleanup_watch.py with explicit confirmation if you decide to apply changes.",
        },
    }
    return report


def print_report(report: dict[str, Any]) -> None:
    """Print a human-readable summary to stdout."""
    summary = report["summary"]
    print("=== review-watchdog-audit ===")
    print(f"Watch jobs: {summary['watchJobsFound']} | P0: {summary['P0']} | P1: {summary['P1']} | P2: {summary['P2']}")

    for f in report["findings"]:
        tokens_info = ""
        if f.get("wasted_tokens") is not None:
            tokens_info = f" | wasted_tokens={f['wasted_tokens']}"
        print(f"- [{f['severity']}] {f['name']} | schedule={f.get('schedule') or '-'} | enabled={f.get('enabled')}{tokens_info}")
        for r in f.get("reasons", []):
            print(f"  - {r}")

    if report.get("duplicates"):
        print("Duplicate groups:")
        for d in report["duplicates"]:
            print(f"  - {d['duplicate']} overlaps with {d['original']}")

    state = report.get("stateAudit", {})
    if state.get("issues"):
        print("State audit issues:")
        for issue in state["issues"]:
            print(f"  - {issue}")


def main() -> int:
    default_jobs = str(DEFAULT_OPENCLAW_DIR / "cron" / "jobs.json")
    default_runs = str(DEFAULT_OPENCLAW_DIR / "cron" / "runs")
    default_state = str(DEFAULT_OPENCLAW_DIR / "memory" / "review-watch.json")

    parser = argparse.ArgumentParser(description="Audit cron review/watch tasks for traffic waste risk.")
    parser.add_argument("--jobs", default=default_jobs, help="Path to cron jobs.json")
    parser.add_argument("--runs-dir", default=default_runs, help="Path to cron run jsonl dir")
    parser.add_argument("--state-file", default=default_state, help="Optional state file path")
    parser.add_argument("--max-run-files", type=int, default=80, help="How many recent run files to scan")
    parser.add_argument("--output", default="review-watchdog-audit-report.json", help="Output report path")
    args = parser.parse_args()

    report = run_audit(
        jobs_path=Path(args.jobs),
        runs_dir=Path(args.runs_dir),
        state_path=Path(args.state_file),
        max_run_files=args.max_run_files,
    )

    out_path = Path(args.output)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {out_path}")
    print_report(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
