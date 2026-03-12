# Changelog

## [0.2.0] - 2026-03-12

### Changed

- **定位重塑**：主职责明确为评估推荐，优先复用上游技能搜索结果，无上游结果时才自行通过 ClawHub 搜索。  
  **Role redefined:** primary responsibility is evaluation and recommendation — reuses upstream skill search results first; only falls back to self-searching ClawHub when no upstream candidates exist.

- **工作流优化**：新增 Step 0（检查上游候选），有结果直接跳至评估，避免重复搜索。  
  **Workflow:** added Step 0 (check for upstream candidates) — skips directly to evaluation when results are already available, avoiding redundant searches.

- **去除强依赖**：移除对特定搜索技能的具名引用，统一改为通用"上游技能搜索"表述。  
  **Decoupled:** removed hard dependency on any specific search skill; all references now use generic "upstream skill search" language.

- **描述精简**：`description` 提炼为中英文双语一句话，涵盖 5 个核心能力：ClawHub 搜索候选、已装技能冲突/重叠分析、替换或共存建议、安装前风险披露、用户确认后执行安装。  
  **Description:** condensed to a single bilingual sentence covering all 5 core capabilities: search via ClawHub, conflict/overlap analysis with installed skills, replace-or-coexist recommendation, pre-install risk disclosure, and install only after explicit user confirmation.

---

## [0.1.1] - 初始版本 / Initial Release

- 基础技能推荐流程：搜索、评估、冲突分析、安装确认  
  Basic recommendation flow: search, evaluate, conflict analysis, install confirmation.
- 支持 ClawHub 作为技能来源  
  ClawHub as the skill source.
