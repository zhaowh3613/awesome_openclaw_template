#!/usr/bin/env python3
"""
Patrol mode for review-watchdog-audit.

Designed to be called by an external scheduler (cron / systemd / OpenClaw timer).
Runs a single audit cycle and exits with a meaningful exit code:

  0 — all clear, no alerts
  1 — alert-level findings detected (printed / written / posted)
  2 — patrol script itself encountered an error

Usage examples:

  # stdout alert (default)
  python patrol.py --alert-threshold P1

  # append to file
  python patrol.py --alert-threshold P1 --alert-method file --alert-file /var/log/watchdog-alerts.jsonl

  # POST to webhook (Discord / Slack / Lark)
  python patrol.py --alert-threshold P0 --alert-method webhook --webhook-url https://hooks.slack.com/...
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from audit_cron_watch import run_audit, print_report
from common import DEFAULT_OPENCLAW_DIR, now_iso

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}


def _severity_meets_threshold(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER.get(severity, 99) <= SEVERITY_ORDER.get(threshold, 99)


def _build_alert(report: dict, threshold: str) -> dict | None:
    """Build an alert payload from a report. Returns None if no alert needed."""
    alert_findings = [
        f for f in report.get("findings", [])
        if _severity_meets_threshold(f.get("severity", "P2"), threshold)
    ]
    if not alert_findings:
        return None

    worst = min(alert_findings, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "P2"), 99))
    total_wasted = sum(f.get("wasted_tokens") or 0 for f in alert_findings)

    summary_parts = [f"Found {len(alert_findings)} abnormal task(s)"]
    if total_wasted > 0:
        summary_parts.append(f"estimated wasted tokens: {total_wasted:,}")

    return {
        "level": worst["severity"],
        "timestamp": now_iso(),
        "summary": ", ".join(summary_parts),
        "findings": [
            {
                "name": f["name"],
                "severity": f["severity"],
                "wasted_tokens": f.get("wasted_tokens"),
                "reasons": f.get("reasons", []),
                "action": "stop immediately" if f["severity"] == "P0" else "tune soon",
            }
            for f in alert_findings
        ],
        "action_hint": "Run stop_cleanup_watch.py --target-severity P0 --apply --confirm STOP_AND_CLEANUP",
    }


# ---------------------------------------------------------------------------
# Alert dispatchers
# ---------------------------------------------------------------------------


def _alert_stdout(alert: dict) -> None:
    print("=== WATCHDOG ALERT ===")
    print(f"Level: {alert['level']}")
    print(f"Time:  {alert['timestamp']}")
    print(f"Summary: {alert['summary']}")
    for f in alert["findings"]:
        tokens = f" | wasted_tokens={f['wasted_tokens']}" if f.get("wasted_tokens") else ""
        print(f"  [{f['severity']}] {f['name']}{tokens}")
        for r in f["reasons"]:
            print(f"    - {r}")
    print(f"Action: {alert['action_hint']}")


def _alert_file(alert: dict, filepath: str) -> None:
    with open(filepath, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(alert, ensure_ascii=False) + "\n")
    print(f"Alert appended to {filepath}")


def _alert_webhook(alert: dict, url: str) -> None:
    payload = json.dumps(alert, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"Webhook responded: {resp.status}")
    except urllib.error.URLError as exc:
        print(f"Webhook failed: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    default_jobs = str(DEFAULT_OPENCLAW_DIR / "cron" / "jobs.json")
    default_runs = str(DEFAULT_OPENCLAW_DIR / "cron" / "runs")
    default_state = str(DEFAULT_OPENCLAW_DIR / "memory" / "review-watch.json")

    parser = argparse.ArgumentParser(description="Patrol mode: single audit cycle with alerting.")
    parser.add_argument("--jobs", default=default_jobs, help="Path to cron jobs.json")
    parser.add_argument("--runs-dir", default=default_runs, help="Path to cron run jsonl dir")
    parser.add_argument("--state-file", default=default_state, help="State file path")
    parser.add_argument("--max-run-files", type=int, default=80, help="Max recent run files to scan")
    parser.add_argument("--alert-threshold", default="P1", choices=["P0", "P1", "P2"], help="Minimum severity to trigger alert")
    parser.add_argument("--alert-method", default="stdout", choices=["stdout", "file", "webhook"], help="How to deliver alerts")
    parser.add_argument("--alert-file", default="watchdog-alerts.jsonl", help="File path for file-mode alerts")
    parser.add_argument("--webhook-url", default="", help="Webhook URL for webhook-mode alerts")
    parser.add_argument("--report-output", default="", help="Optionally save full report to this path")
    args = parser.parse_args()

    try:
        report = run_audit(
            jobs_path=Path(args.jobs),
            runs_dir=Path(args.runs_dir),
            state_path=Path(args.state_file),
            max_run_files=args.max_run_files,
        )
    except Exception as exc:
        print(f"Patrol error: {exc}", file=sys.stderr)
        return 2

    # optionally save full report
    if args.report_output:
        Path(args.report_output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    alert = _build_alert(report, args.alert_threshold)
    if alert is None:
        print("Patrol OK — no alerts.")
        return 0

    # dispatch alert
    if args.alert_method == "stdout":
        _alert_stdout(alert)
    elif args.alert_method == "file":
        _alert_file(alert, args.alert_file)
    elif args.alert_method == "webhook":
        if not args.webhook_url:
            print("Error: --webhook-url required for webhook mode.", file=sys.stderr)
            return 2
        _alert_webhook(alert, args.webhook_url)

    # also print summary to stdout regardless of method
    if args.alert_method != "stdout":
        print(f"Alert dispatched via {args.alert_method}: {alert['summary']}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
