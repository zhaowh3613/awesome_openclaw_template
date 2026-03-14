#!/usr/bin/env python3
"""
Apply stop/cleanup plan from review-watchdog-audit report.

Safety:
- Requires --apply and --confirm "STOP_AND_CLEANUP"
- Always creates backup before mutating jobs.json
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_OPENCLAW_DIR,
    extract_job_name,
    extract_jobs,
    now_stamp,
    safe_read_json,
    save_jobs,
)


def main() -> int:
    default_jobs = str(DEFAULT_OPENCLAW_DIR / "cron" / "jobs.json")

    parser = argparse.ArgumentParser(description="Stop/cleanup invalid cron watch tasks")
    parser.add_argument("--report", default="review-watchdog-audit-report.json", help="Audit report path")
    parser.add_argument("--jobs", default=default_jobs, help="Cron jobs file")
    parser.add_argument("--state-files", nargs="*", default=[], help="Optional stale state files to remove")
    parser.add_argument("--mode", choices=["disable", "delete"], default="disable", help="How to stop target jobs")
    parser.add_argument("--target-severity", default="P0", help="Comma-separated severity levels to target (e.g. P0,P1)")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes")
    parser.add_argument("--confirm", default="", help="Must be STOP_AND_CLEANUP to apply")
    args = parser.parse_args()

    report_path = Path(args.report)
    jobs_path = Path(args.jobs)

    report = safe_read_json(report_path)
    if report is None:
        raise SystemExit(f"Report not found or unreadable: {report_path}")
    if not jobs_path.exists():
        raise SystemExit(f"Jobs file not found: {jobs_path}")

    target_severities = {s.strip() for s in args.target_severity.split(",")}
    findings = report.get("findings", []) if isinstance(report, dict) else []
    target_names = {
        f.get("name")
        for f in findings
        if isinstance(f, dict)
        and f.get("severity") in target_severities
        and isinstance(f.get("name"), str)
    }

    # compute token savings estimate
    total_wasted = sum(
        f.get("wasted_tokens") or 0
        for f in findings
        if isinstance(f, dict) and f.get("name") in target_names
    )

    print("=== stop-cleanup plan ===")
    print(f"Target severity: {args.target_severity}")
    print(f"Target jobs: {sorted(target_names) if target_names else '[]'}")
    print(f"Mode: {args.mode}")
    if total_wasted > 0:
        print(f"Estimated token savings: {total_wasted:,}")

    if not args.apply:
        print("Dry-run only. Re-run with --apply --confirm STOP_AND_CLEANUP")
        return 0

    if args.confirm != "STOP_AND_CLEANUP":
        raise SystemExit("Confirmation missing or invalid. Use --confirm STOP_AND_CLEANUP")

    backup_path = jobs_path.with_suffix(jobs_path.suffix + f".bak.{now_stamp()}")
    shutil.copy2(jobs_path, backup_path)
    print(f"Backup created: {backup_path}")

    payload = safe_read_json(jobs_path)
    if payload is None:
        raise SystemExit(f"Failed to read jobs file: {jobs_path}")
    jobs, schema = extract_jobs(payload)

    new_jobs: list[dict[str, Any]] = []
    changed: list[tuple[str, str]] = []
    for idx, job in enumerate(jobs):
        if not isinstance(job, dict):
            new_jobs.append(job)
            continue
        name = extract_job_name(job, idx)
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

    removed_states: list[str] = []
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

    if total_wasted > 0:
        print(f"Estimated token savings: {total_wasted:,} tokens")

    print("Done. To rollback, restore backup:")
    print(f"cp {backup_path} {jobs_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
