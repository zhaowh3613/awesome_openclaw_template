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
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WATCH_KEYWORDS = ("review", "watch", "pr", "pull request", "github")
ERROR_402_PATTERNS = ("402", "quota", "payment required", "zenmux")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def score_watch_job(job: dict[str, Any]) -> int:
    text = json.dumps(job, ensure_ascii=False).lower()
    score = 0
    for kw in WATCH_KEYWORDS:
        if kw in text:
            score += 1
    return score


def extract_job_name(job: dict[str, Any], idx: int) -> str:
    for key in ("id", "name", "jobId", "label"):
        if isinstance(job.get(key), str) and job.get(key).strip():
            return job[key].strip()
    return f"job-{idx}"


@dataclass
class JobFinding:
    name: str
    score: int
    severity: str
    reasons: list[str]
    schedule: str | None
    enabled: bool | None


def classify_job(job: dict[str, Any], name: str, score: int, run_lines: list[str]) -> JobFinding:
    reasons: list[str] = []
    failures = 0
    err402 = 0

    for line in run_lines:
        lower = line.lower()
        if any(p in lower for p in ("error", "failed", "exception", "exit code")):
            failures += 1
        if any(p in lower for p in ERROR_402_PATTERNS):
            err402 += 1

    if score <= 0:
        severity = "P2"
        reasons.append("No strong watch/review signals in job definition.")
    else:
        if err402 >= 3:
            severity = "P0"
            reasons.append(f"Detected repeated quota/402-like failures ({err402} matches).")
        elif failures >= 3:
            severity = "P1"
            reasons.append(f"Detected repeated failures ({failures} suspicious log lines).")
        else:
            severity = "P2"
            reasons.append("No obvious repeat-failure pattern found in sampled logs.")

    if score > 0 and not run_lines:
        reasons.append("No recent run logs found for this task; verify whether it is stale or inactive.")

    schedule = None
    for key in ("schedule", "cron", "interval", "every"):
        if job.get(key) is not None:
            schedule = str(job.get(key))
            break

    enabled = job.get("enabled") if isinstance(job.get("enabled"), bool) else None

    return JobFinding(
        name=name,
        score=score,
        severity=severity,
        reasons=reasons,
        schedule=schedule,
        enabled=enabled,
    )


def list_recent_run_lines(runs_dir: Path, max_files: int, grep_name: str) -> list[str]:
    if not runs_dir.exists():
        return []
    files = sorted(runs_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]
    lines: list[str] = []
    pattern = re.compile(re.escape(grep_name), re.IGNORECASE)
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if pattern.search(text):
            lines.extend(text.splitlines())
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit cron review/watch tasks for traffic waste risk.")
    parser.add_argument("--jobs", default="/root/.openclaw/cron/jobs.json", help="Path to cron jobs.json")
    parser.add_argument("--runs-dir", default="/root/.openclaw/cron/runs", help="Path to cron run jsonl dir")
    parser.add_argument("--state-file", default="/root/.openclaw/memory/review-watch.json", help="Optional state file path")
    parser.add_argument("--max-run-files", type=int, default=80, help="How many recent run files to scan")
    parser.add_argument("--output", default="review-watchdog-audit-report.json", help="Output report path")
    args = parser.parse_args()

    jobs_path = Path(args.jobs)
    runs_dir = Path(args.runs_dir)
    state_path = Path(args.state_file)
    out_path = Path(args.output)

    jobs_payload = safe_read_json(jobs_path)
    jobs = []
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
        run_lines = list_recent_run_lines(runs_dir, args.max_run_files, name)
        findings.append(classify_job(job, name, score, run_lines))

    p0 = [f for f in findings if f.severity == "P0"]
    p1 = [f for f in findings if f.severity == "P1"]
    p2 = [f for f in findings if f.severity == "P2"]

    report = {
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
        "stateFileExists": state_path.exists(),
        "recommendation": {
            "action": "stop-p0-first" if p0 else ("tune-p1" if p1 else "keep"),
            "note": "Run stop_cleanup_watch.py with explicit confirmation if you decide to apply changes.",
        },
    }

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=== review-watchdog-audit ===")
    print(f"Report: {out_path}")
    print(f"Watch jobs: {len(findings)} | P0: {len(p0)} | P1: {len(p1)} | P2: {len(p2)}")
    for f in findings:
        print(f"- [{f.severity}] {f.name} | schedule={f.schedule or '-'} | enabled={f.enabled}")
        for r in f.reasons:
            print(f"  - {r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
