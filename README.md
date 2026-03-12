# Awesome OpenClaw Templates

English | [中文](#中文介绍)

A curated collection of practical templates and agent presets for OpenClaw.

- Helps you bootstrap multi-agent workflows quickly
- Includes ready-to-use channel bindings and role setup patterns
- Focuses on real production-friendly defaults

## Author

**VinceZ.辉**  
X: <https://x.com/zhaowh3613>

## Project Overview

This repository provides reusable OpenClaw templates, currently focused on:

- **Discord multi-agent collaboration**
- **Coder + Reviewer workflow setup**
- **Channel routing and allowlist examples**

## Included Template

### Multi-Agent: Discord Integration

**File:** `multi_agents/discord_multi _agents.json`

This template sets up two collaborative agents on Discord:

- **Coder** (`discord-agent-coder`) — implementation and delivery
- **Reviewer** (`discord-agent-reviewer`) — quality gate and review flow

Both agents are configured with independent bindings, workspaces, and channel routing.

## Quick Start

1. Copy the template and replace placeholders:
   - `<discord-bot-coder-token>`
   - `<discord-bot-reviewer-token>`
   - `<discord-server-id>`
   - `<coder-bot-channel-id>`
   - `<reviewer-bot-channel-id>`
2. Put it into your OpenClaw config directory.
3. Start OpenClaw and verify both agents are online.

## Contributing

PRs are welcome for:

- New templates
- Better workflow presets
- Localization and documentation improvements

---

## 中文介绍

这是一个面向 OpenClaw 的高质量模板仓库，帮助你快速搭建可落地的 Agent 工作流。

### 项目目标

- 提供开箱即用的多 Agent 配置模板
- 降低频道绑定、权限控制、路由策略的上手成本
- 沉淀适合真实协作场景的最佳实践

### 当前内容

目前主要包含 **Discord 多 Agent 协作模板**，覆盖：

- Coder + Reviewer 双角色协同
- 独立账号/频道绑定
- allowlist 访问控制示例

### 快速使用

1. 复制模板文件并替换占位符（Bot Token、频道 ID、服务器 ID）。
2. 放入 OpenClaw 配置目录。
3. 启动 OpenClaw，确认两个 Agent 均上线。

### 作者

**VinceZ.辉**  
X：<https://x.com/zhaowh3613>
