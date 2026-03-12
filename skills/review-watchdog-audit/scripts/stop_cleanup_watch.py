#!/usr/bin/env python3
"""
Apply stop/cleanup plan from review-watchdog-audit report.

Safety:
- Requires --apply and --confirm "STOP_AND_CLEANUP"
- Always creates backup before mutating jobs.json
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_jobs(payload: Any) -> tuple[list[dict[str, Any]], str]:
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload["jobs"], "dict"
    if isinstance(payload, list):
        return payload, "list"
    raise ValueError("Unsupported jobs schema")


def save_jobs(path: Path, original: Any, jobs: list[dict[str, Any]], schema: str) -> None:
    if schema == "dict":
        original["jobs"] = jobs
        content = original
    else:
        content = jobs
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def job_name(job: dict[str, Any], idx: int) -> str:
    for k in ("id", "name", "jobId", "label"):
        v = job.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return f"job-{idx}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop/cleanup invalid cron watch tasks")
    parser.add_argument("--report", default="review-watchdog-audit-report.json", help="Audit report path")
    parser.add_argument("--jobs", default="/root/.openclaw/cron/jobs.json", help="Cron jobs file")
    parser.add_argument("--state-files", nargs="*", default=[], help="Optional stale state files to remove")
    parser.add_argument("--mode", choices=["disable", "delete"], default="disable", help="How to stop target jobs")
    parser.add_argument("--target-severity", default="P0", help="Only apply to findings of this severity")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes")
    parser.add_argument("--confirm", default="", help="Must be STOP_AND_CLEANUP to apply")
    args = parser.parse_args()

    report_path = Path(args.report)
    jobs_path = Path(args.jobs)

    if not report_path.exists():
        raise SystemExit(f"Report not found: {report_path}")
    if not jobs_path.exists():
        raise SystemExit(f"Jobs file not found: {jobs_path}")

    report = load_json(report_path)
    findings = report.get("findings", []) if isinstance(report, dict) else []
    target_names = {
        f.get("name")
        for f in findings
        if isinstance(f, dict) and f.get("severity") == args.target_severity and isinstance(f.get("name"), str)
    }

    print("=== stop-cleanup plan ===")
    print(f"Target severity: {args.target_severity}")
    print(f"Target jobs: {sorted(target_names) if target_names else '[]'}")
    print(f"Mode: {args.mode}")

    if not args.apply:
        print("Dry-run only. Re-run with --apply --confirm STOP_AND_CLEANUP")
        return 0

    if args.confirm != "STOP_AND_CLEANUP":
        raise SystemExit("Confirmation missing or invalid. Use --confirm STOP_AND_CLEANUP")

    backup_path = jobs_path.with_suffix(jobs_path.suffix + f".bak.{now_stamp()}")
    shutil.copy2(jobs_path, backup_path)
    print(f"Backup created: {backup_path}")

    payload = load_json(jobs_path)
    jobs, schema = extract_jobs(payload)

    new_jobs: list[dict[str, Any]] = []
    changed = []
    for idx, job in enumerate(jobs):
        if not isinstance(job, dict):
            new_jobs.append(job)
            continue
        name = job_name(job, idx)
        if name not in target_names:
            new_jobs.append(job)
            continue

        if args.mode == "delete":
            changed.append((name, "deleted"))
            continue

        job["enabled"] = False
        job["disabledBy"] = "review-watchdog-audit"
        job["disabledAt"] = datetime.now(timezone.utc).isoformat()
        new_jobs.append(job)
        changed.append((name, "disabled"))

    save_jobs(jobs_path, payload, new_jobs, schema)

    removed_states = []
    for s in args.state_files:
        p = Path(s)
        if p.exists() and p.is_file():
            p.unlink()
            removed_states.append(str(p))

    print("Changes applied:")
    for name, action in changed:
        print(f"- {name}: {action}")
    if removed_states:
        print("Removed state files:")
        for p in removed_states:
            print(f"- {p}")

    print("Done. To rollback, restore backup:")
    print(f"cp {backup_path} {jobs_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
