# review-watchdog-audit

## 中文介绍

`review-watchdog-audit` 是一个定时任务审计技能，专门检查 PR 监控类 cron 任务（如 `review-group-pr-watch`）的运行健康状况，识别无效流量消耗、重复失败、冗余监控等问题，并提供一键停止与清理方案。

核心能力：

- 盘点所有 cron 监控任务的配置与状态
- 分析近期执行日志，识别失败模式与重复运行
- 验证任务有效性（是否处理了真正的新更新）
- 按严重程度分级：P0（立即停止）/ P1（尽快调优）/ P2（保留）
- 用户确认后执行一键停止与清理

适用场景：

- "我的 cron 任务是不是在烧流量？"
- "哪些监控任务应该停掉？"
- "帮我检查一下定时任务的健康状况"
- "一键清理无效的 PR 监控"

**注意：** 仅手动触发，不会自动后台运行。

---

## English Overview

`review-watchdog-audit` is a cron task auditing skill that inspects PR watch tasks (e.g. `review-group-pr-watch`) for invalid traffic burn, repeated failures, duplicate monitors, and ineffective runs — then provides a one-click stop-and-cleanup plan.

Key capabilities:

- Inventory all cron watch tasks with their config and state
- Analyze recent execution logs for failure patterns and burst behavior
- Validate whether tasks do meaningful work or repeatedly process stale data
- Classify risk by severity: P0 (stop now) / P1 (tune soon) / P2 (keep)
- Execute stop-and-cleanup after explicit user confirmation

Typical use cases:

- "Are my cron tasks burning traffic?"
- "Which watch tasks should be stopped?"
- "Audit the health of my scheduled tasks"
- "One-click cleanup of ineffective PR monitors"

**Note:** Manual trigger only — does not run automatically in the background.

---

## Bundled Scripts

| Script | Purpose |
|---|---|
| `scripts/audit_cron_watch.py` | Read-only audit, outputs JSON report |
| `scripts/stop_cleanup_watch.py` | Stop/cleanup execution (requires `--apply --confirm` flags) |

---

## Author

VinceZ.辉 (<https://x.com/zhaowh3613>)
