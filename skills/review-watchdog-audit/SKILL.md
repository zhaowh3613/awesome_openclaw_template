---
name: review-watchdog-audit
description: Patrol and audit scheduled review/watch cron tasks for wasted token consumption, repeated failures, duplicate monitors, cursor anomalies, and ineffective runs. Supports manual audit, automated patrol mode with alerting (stdout / file / webhook), and one-click stop-and-cleanup. Use when users ask to inspect cron waste, check whether tasks should be stopped, set up periodic health checks, or request a stop-and-cleanup plan.
---

# review-watchdog-audit

Inspect cron-based PR watch tasks, detect wasted token consumption, and provide a stop/cleanup recommendation with evidence.

## Scope

Audit these layers:
- Cron config (`cron/jobs.json`)
- Execution logs (`cron/runs/*.jsonl`)
- Watch state files (for example `memory/review-watch.json`)
- Recent failure patterns (especially quota/402-like failures)
- Token consumption analysis (total vs wasted)
- Duplicate task detection
- Cursor/checkpoint health

## Path Configuration

All scripts default to `~/.openclaw/` (or `$OPENCLAW_DIR` if set). Override per-path via CLI flags.

## Manual Audit (One-off)

Run only after explicit user request.

### Read-only audit

```bash
python skills/review-watchdog-audit/scripts/audit_cron_watch.py \
  --jobs ~/.openclaw/cron/jobs.json \
  --runs-dir ~/.openclaw/cron/runs \
  --state-file ~/.openclaw/memory/review-watch.json \
  --output review-watchdog-audit-report.json
```

### Stop/Cleanup (explicit confirmation required)

Dry run first:

```bash
python skills/review-watchdog-audit/scripts/stop_cleanup_watch.py \
  --report review-watchdog-audit-report.json \
  --jobs ~/.openclaw/cron/jobs.json
```

Apply changes only after user confirms (supports comma-separated severities):

```bash
python skills/review-watchdog-audit/scripts/stop_cleanup_watch.py \
  --report review-watchdog-audit-report.json \
  --jobs ~/.openclaw/cron/jobs.json \
  --mode disable \
  --target-severity P0,P1 \
  --apply \
  --confirm STOP_AND_CLEANUP
```

## Patrol Mode (Scheduled)

Use `patrol.py` for automated periodic health checks. It runs one audit cycle and exits with:
- **exit 0** — all clear, no alerts
- **exit 1** — alert-level findings detected
- **exit 2** — patrol script error

### Alert Methods

| Method | Flag | Description |
|--------|------|-------------|
| stdout | `--alert-method stdout` | Print alert summary (default, works with OpenClaw log capture) |
| file | `--alert-method file --alert-file <path>` | Append JSON alert to a file (JSONL format) |
| webhook | `--alert-method webhook --webhook-url <url>` | POST JSON to Discord/Slack/Lark webhook |

### Examples

```bash
# Single patrol check, alert on P1+
python skills/review-watchdog-audit/scripts/patrol.py \
  --alert-threshold P1 \
  --alert-method stdout

# Patrol with webhook alert and full report saved
python skills/review-watchdog-audit/scripts/patrol.py \
  --alert-threshold P0 \
  --alert-method webhook \
  --webhook-url https://hooks.slack.com/services/xxx \
  --report-output /tmp/latest-audit.json
```

### Cron scheduling example

```bash
# Every 30 minutes, alert on P1+ via webhook
*/30 * * * * python skills/review-watchdog-audit/scripts/patrol.py \
  --alert-threshold P1 \
  --alert-method webhook \
  --webhook-url https://hooks.example.com/watchdog
```

## Audit Workflow

### 1) Collect task inventory

For each relevant task (for example `review-group-pr-watch`), capture:
- name
- schedule frequency
- target repos/org
- model/runtime settings
- enabled/disabled state

### 2) Inspect recent executions

Check recent runs and summarize:
- success/failure ratio
- common error types (especially 402/quota)
- repeated failure streaks (consecutive failures)
- whether backoff is present between failures
- average run duration and burst/spike behavior

### 3) Token consumption analysis

For each task:
- Total tokens consumed across recent runs
- Tokens consumed by failed runs (= **wasted tokens**)
- Waste ratio (wasted / total)
- P0 trigger: waste ratio > 50%
- P1 trigger: waste ratio > 30%

### 4) Validate effectiveness

Determine whether the task does meaningful work:
- Does it process truly new updates?
- Does it repeatedly review old PRs?
- Does state cursor regress or fail to advance?
- Are there duplicate tasks monitoring same scope?

### 5) Classify risk

Use severity:
- **P0 (stop now)**: clear quota burn, repeat failures >= 5 consecutive, waste ratio > 50%, cursor regression, no useful output
- **P1 (tune soon)**: waste exists but task still partially useful, waste ratio > 30%, stale cursor > 7 days, duplicate tasks
- **P2 (keep)**: healthy task with acceptable cost/benefit

### 6) Produce action plan

For each task provide one decision:
- keep
- pause
- delete
- merge with another task

Include rationale, token savings estimate, and rollback note.

## One-Click Stop & Cleanup Plan

When user confirms execution, perform in this order:
1. Backup `cron/jobs.json`
2. Disable/delete P0 tasks (or P0+P1 with `--target-severity P0,P1`)
3. Optionally clean stale state files linked to disabled tasks
4. Report estimated token savings
5. Record audit decision to memory for traceability
6. Return summary + rollback path

Never execute stop/cleanup without explicit confirmation.

## Report Template

- Task summary table (name / frequency / status / last result / wasted tokens)
- Token consumption breakdown (total / wasted / waste ratio per task)
- Evidence snippets (timestamps, error codes, duplicate patterns, streak counts)
- State audit results (cursor value, staleness, regression, duplicate PRs)
- Duplicate task groups (overlapping scopes)
- Recommended action per task (keep/pause/delete/merge)
- Confirmation prompt for one-click stop+cleanup

## Safety Guardrails

- Audit first, act second.
- Keep reversible changes (backup before mutation).
- If confidence is low, recommend pause over delete.
- Do not remove healthy tasks without user approval.
- Patrol mode is read-only; it never modifies cron config.
