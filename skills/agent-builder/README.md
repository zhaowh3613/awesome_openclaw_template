# agent-builder

## 中文介绍

`agent-builder` 是一个从零构建完整 OpenClaw Agent Workspace 的技能。当用户描述想要的 Agent 角色（产品经理、工程师、研究员、设计师等）时，自动生成所有必需文件，并通过 ClawHub 搜索安装角色相关技能。

核心能力：

- 角色画像分析：提炼核心职责、思维模式、气质关键词、能力边界
- 自动预装 `find-skills` 并通过 ClawHub 查询角色相关技能
- 生成 9 个标准化文件（SOUL / IDENTITY / USER / TOOLS / AGENTS / HEARTBEAT / MEMORY / BOOTSTRAP / 当日日志）
- 所有文件中英文双版本输出
- 严格分层铁律：每个文件只负责一件事，违反即返工

适用场景：

- "帮我建一个产品经理 Agent"
- "我需要一个代码审查专用的 Agent workspace"
- "从零搭建一个数据分析 Agent"

---

## English Overview

`agent-builder` creates a complete OpenClaw Agent Workspace from scratch. When a user describes the agent role they want (PM, engineer, researcher, designer, etc.), it generates all required files with strict layer separation and searches ClawHub for role-relevant skills.

Key capabilities:

- Role profiling: extract core responsibilities, mental model, vibe keywords, capability boundaries
- Auto-install `find-skills` and query ClawHub for role-relevant skills
- Generate 9 standardized files (SOUL / IDENTITY / USER / TOOLS / AGENTS / HEARTBEAT / MEMORY / BOOTSTRAP / daily log)
- Bilingual output (Chinese + English) for every file
- Strict separation rules: each file has exactly one responsibility

Typical use cases:

- "Build me a PM agent"
- "I need a code review agent workspace"
- "Set up a data analysis agent from scratch"

---

## Generated Workspace Structure

```
workspace-{name}/
├── AGENTS.md + AGENTS.en.md
├── BOOTSTRAP.md + BOOTSTRAP.en.md
├── HEARTBEAT.md + HEARTBEAT.en.md
├── IDENTITY.md + IDENTITY.en.md
├── MEMORY.md + MEMORY.en.md
├── SOUL.md + SOUL.en.md
├── TOOLS.md + TOOLS.en.md
├── USER.md + USER.en.md
├── memory/
│   └── YYYY-MM-DD.md
└── skills/
    ├── find-skills/
    └── {other-skills}/
```

---

## Author

VinceZ.辉 (<https://x.com/zhaowh3613>)
