# Changelog

## [0.2.3] - 2026-03-15

### Added / 新增

- **新技能：skill-upgrade-checker (v0.1.0)**：检查已安装技能的可用升级，通过语义版本比较和变更日志解读提供风险评估，经用户确认后执行一键升级。
  **New skill: skill-upgrade-checker (v0.1.0):** checks installed skills for available upgrades, provides risk assessment via semver comparison and changelog interpretation, and executes upgrades after explicit user confirmation.

---

## [0.2.2] - 2026-03-12

### Added / 新增

- **前置条件声明**：新增 `## Prerequisites` 章节，明确 `clawhub` CLI 必须安装并在 PATH 中可用，需提前执行 `clawhub login` 完成认证，凭证由 CLI 自管理，本技能不读取任何环境变量。  
  **Prerequisites section:** documents that the `clawhub` CLI must be installed and in PATH, `clawhub login` must be run in advance, credentials are managed by the CLI itself, and no environment variables are required by this skill.

- **元数据补全**：`_meta.json` 新增 `requires` 字段，声明依赖二进制（`clawhub`）、认证方式及最小权限范围。  
  **Metadata:** added `requires` field to `_meta.json` declaring the required binary (`clawhub`), authentication method, and minimum permission scope.

### Changed / 调整

- **已安装技能枚举机制明确**：Step 3 明确通过 `clawhub list` 获取已安装技能列表，不再模糊表述为"inspect installed skills"。  
  **Installed skill enumeration:** Step 3 now explicitly uses `clawhub list` to enumerate installed skills, replacing the vague "inspect installed skills" wording.

- **风险信号具体化**：Pre-Install Gate（Step 5）将"notable risk signals"从模糊描述替换为 5 条可量化判断标准：安装数 < 10、最后更新 > 6 个月、需要宽泛权限、发布 < 2 周、无可验证作者身份。  
  **Risk signals defined:** Pre-Install Gate (Step 5) replaces vague "notable risk signals" with 5 concrete, checkable criteria: install count < 10, last update > 6 months ago, broad permissions required, published < 2 weeks ago, no verified author identity.

---

## [0.2.0] - 2026-03-12

### Changed / 调整

- **定位重塑**：主职责明确为评估推荐，优先复用上游技能搜索结果，无上游结果时才自行通过 ClawHub 搜索。  
  **Role redefined:** primary responsibility is evaluation and recommendation — reuses upstream skill search results first; only falls back to self-searching ClawHub when no upstream candidates exist.

- **工作流优化**：新增 Step 0（检查上游候选），有结果直接跳至评估，避免重复搜索。  
  **Workflow:** added Step 0 (check for upstream candidates) — skips directly to evaluation when results are already available, avoiding redundant searches.

- **去除强依赖**：移除对特定搜索技能的具名引用，统一改为通用"上游技能搜索"表述。  
  **Decoupled:** removed hard dependency on any specific search skill; all references now use generic "upstream skill search" language.

- **描述精简**：`description` 提炼为中英文双语一句话，涵盖 5 个核心能力：ClawHub 搜索候选、已装技能冲突/重叠分析、替换或共存建议、安装前风险披露、用户确认后执行安装。  
  **Description:** condensed to a single bilingual sentence covering 5 core capabilities: search via ClawHub, conflict/overlap analysis, replace-or-coexist recommendation, pre-install risk disclosure, and install only after explicit user confirmation.

---

## [0.1.1] - 初始版本 / Initial Release

- 基础技能推荐流程：搜索、评估、冲突分析、安装确认  
  Basic recommendation flow: search, evaluate, conflict analysis, install confirmation.
- 支持 ClawHub 作为技能来源  
  ClawHub as the skill source.
