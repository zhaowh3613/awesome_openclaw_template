---
name: review-watchdog-audit
description: Audit scheduled review/watch cron tasks (especially review-group-pr-watch) for invalid traffic burn, repeated failures, duplicate monitors, and ineffective runs. Use when users ask to inspect cron waste, check whether tasks should be stopped, or request a one-click stop-and-cleanup plan. Manual trigger only; do not run automatically.
---

# review-watchdog-audit

Inspect cron-based PR watch tasks and provide a stop/cleanup recommendation with evidence.

## Scope

Audit these layers:
- Cron config (`cron/jobs.json`)
- Execution logs (`cron/runs/*.jsonl`)
- Watch state files (for example `memory/review-watch.json`)
- Recent failure patterns (especially quota/402-like failures)

## Manual Trigger Requirement

Run only after explicit user request.
Do not run in background automatically.

## Scripted Operations

Use bundled scripts for deterministic execution.

### Read-only audit

```bash
python skills/review-watchdog-audit/scripts/audit_cron_watch.py \
  --jobs /root/.openclaw/cron/jobs.json \
  --runs-dir /root/.openclaw/cron/runs \
  --state-file /root/.openclaw/memory/review-watch.json \
  --output review-watchdog-audit-report.json
```

### Stop/Cleanup (explicit confirmation required)

Dry run first:

```bash
python skills/review-watchdog-audit/scripts/stop_cleanup_watch.py \
  --report review-watchdog-audit-report.json \
  --jobs /root/.openclaw/cron/jobs.json
```

Apply changes only after user confirms:

```bash
python skills/review-watchdog-audit/scripts/stop_cleanup_watch.py \
  --report review-watchdog-audit-report.json \
  --jobs /root/.openclaw/cron/jobs.json \
  --mode disable \
  --target-severity P0 \
  --apply \
  --confirm STOP_AND_CLEANUP
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
- common error types
- repeated failure streaks
- whether backoff is present
- average run duration and burst behavior

### 3) Validate effectiveness

Determine whether the task does meaningful work:
- Does it process truly new updates?
- Does it repeatedly review old PRs?
- Does state cursor regress or fail to advance?
- Are there duplicate tasks monitoring same scope?

### 4) Classify risk

Use severity:
- **P0 (stop now)**: clear quota burn, repeat failures, no useful output
- **P1 (tune soon)**: waste exists but task still partially useful
- **P2 (keep)**: healthy task with acceptable cost/benefit

### 5) Produce action plan

For each task provide one decision:
- keep
- pause
- delete
- merge with another task

Include rationale and rollback note.

## One-Click Stop & Cleanup Plan (Design)

When user confirms execution, perform in this order:
1. Backup `cron/jobs.json`
2. Disable/delete P0 tasks
3. Optionally clean stale state files linked to disabled tasks
4. Record audit decision to memory for traceability
5. Return summary + rollback path

Never execute stop/cleanup without explicit confirmation.

## Report Template

- Task summary table (name / frequency / status / last result)
- Evidence snippets (timestamps, error codes, duplicate patterns)
- Waste diagnosis (why traffic is being burned)
- Recommended action per task (keep/pause/delete/merge)
- Confirmation prompt for one-click stop+cleanup

## Safety Guardrails

- Audit first, act second.
- Keep reversible changes (backup before mutation).
- If confidence is low, recommend pause over delete.
- Do not remove healthy tasks without user approval.
