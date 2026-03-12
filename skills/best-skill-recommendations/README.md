# best-skill-recommendations

## 中文介绍

`best-skill-recommendations` 是一个面向技能商店决策的工作流技能，用于在“查找、推荐、安装、更新”技能时提供高质量、可审计的决策支持。

它不仅做候选技能搜索，还会：

- 优先使用 `skillhub`，失败时自动回退 `clawhub`
- 评估已安装技能与新候选的冲突/重叠关系
- 给出“卸载替换”或“并存共用”的建议
- 安装前强制披露来源、版本和风险信号
- 在用户确认后再执行安装

适用场景：

- “这个需求装哪个技能最合适？”
- “我现在的技能会不会和新技能冲突？”
- “应该替换旧技能还是共存？”

---

## English Overview

`best-skill-recommendations` is a workflow skill for high-confidence skill-store decisions when users need to discover, compare, install, or update skills.

It goes beyond search and recommendation by adding:

- `skillhub`-first discovery with automatic `clawhub` fallback
- Installed-skill compatibility and conflict analysis
- Replace-vs-coexist decision support
- Mandatory pre-install disclosure (source, version, risk signals)
- Explicit user confirmation before install actions

Typical use cases:

- “What is the best skill for this task?”
- “Will this new skill conflict with what I already installed?”
- “Should I replace an existing skill or keep both?”

---

## Author

VinceZ.辉 (<https://x.com/zhaowh3613>)
