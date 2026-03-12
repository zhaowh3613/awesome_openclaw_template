# best-skill-recommendations

## 中文介绍

`best-skill-recommendations` 是一个技能综合评估与推荐技能，支持从腾讯 SkillHub 和 ClawHub 双源获取候选技能，进行冲突检测、替换/共存决策，并在用户确认后安全安装。

### 关于腾讯 SkillHub

[SkillHub](https://skillhub.tencent.com/) 是腾讯官方推出的 AI Agent 技能市场，提供：

- 可搜索的技能注册表（支持公有和私有技能）
- 版本管理、作者归属和安装统计
- CLI 工具（`skillhub`）用于搜索、安装、更新和发布技能

best-skill-recommendations技能以 `skillhub` 作为**首选发现和安装渠道**，不可用或无匹配时自动回退到 `clawhub`。

**安装 SkillHub CLI：**

```bash
curl -fsSL https://skillhub-1251783334.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash
```

| 操作 | 命令 |
|---|---|
| 搜索技能 | `skillhub search <关键词>` |
| 安装技能 | `skillhub install <技能>` |
| 更新技能 | `skillhub update <技能>` |
| 查看已安装 | `skillhub list` |
| 卸载技能 | `skillhub uninstall <技能>` |

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

`best-skill-recommendations` is a skill evaluation and recommendation engine — it aggregates candidates from Tencent SkillHub and ClawHub, detects install conflicts, recommends replace-or-coexist strategies, and executes safe installs with explicit user confirmation.

### About Tencent SkillHub

[SkillHub](https://skillhub.tencent.com/) is Tencent's official AI Agent skill marketplace, providing:

- A searchable registry of curated skills (public and private)
- Version management, author attribution, and install metrics
- CLI tooling (`skillhub`) for search, install, update, and publish
- Conflict-aware dependency resolution between skills

This skill uses `skillhub` as the **preferred discovery and install channel**, falling back to `clawhub` when unavailable or no match is found.

**Install SkillHub CLI:**

```bash
curl -fsSL https://skillhub-1251783334.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash
```

| Action | Command |
|---|---|
| Search skills | `skillhub search <keywords>` |
| Install a skill | `skillhub install <skill>` |
| Update a skill | `skillhub update <skill>` |
| List installed | `skillhub list` |
| Uninstall | `skillhub uninstall <skill>` |

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
