---
name: agent-builder
description: Build a complete openclaw agent workspace from scratch. Use when user describes a role they want an agent to play — PM, engineer, researcher, designer, etc. Generates all required files with strict layer separation, auto-installs find-skills, and searches clawhub for relevant skills.
---

# agent-builder

从零构建一个完整的 openclaw agent workspace。
Build a complete openclaw agent workspace from scratch.

---

## 触发条件 / Trigger

用户描述想要的 agent 角色时启动此技能。
Activate when the user describes an agent role they want to create.

---

## 执行流程 / Execution Flow

### Step 1：角色画像 / Role Profiling

分析目标角色，提炼以下内容：
Analyze the target role and extract:

- **核心职责 / Core Responsibilities** — 这个角色做什么 / What this role does
- **思维模式 / Mental Model** — 怎么做决定，优先级如何排 / How decisions are made
- **气质关键词 / Vibe Keywords** — 3–5个词定义风格 / 3–5 words defining the style
- **能力边界 / Capability Boundary** — 不该做什么，越界要止步 / What it must NOT do
- **所需技能 / Required Skills** — 需要哪些 skill 支撑 / Which skills to install

---

### Step 2：自动安装 find-skills + 查询 clawhub

**所有新 workspace 必须预装 find-skills。**
**All new workspaces must have find-skills pre-installed.**

```bash
# 将 find-skills 复制到新 workspace 的 skills/ 目录
# Copy find-skills into the new workspace's skills/ directory
cp -r <source>/skills/find-skills  workspace-{代称}/skills/find-skills
```

安装完成后，**立即用 find-skills 查询角色相关技能**：
After install, **immediately query clawhub for role-relevant skills**:

```bash
# 根据角色类型搜索，关键词参考下表
npx skills find [role-keywords]
```

| 角色类型 / Role | 推荐查询词 / Search Keywords |
|----------------|---------------------------|
| PM / 产品经理 | `product prd roadmap` |
| 工程师 / Engineer | `code review github testing` |
| 研究员 / Researcher | `research web pdf summarize` |
| 设计师 / Designer | `ui design figma accessibility` |
| 运营 / Operations | `analytics workflow automation` |
| 数据分析 / Data | `data analysis visualization sql` |

查询结果呈现给用户，确认后安装推荐技能：
Present results to user, then install confirmed skills:

```bash
npx skills add <owner/repo@skill-name> -g -y
```

未找到匹配时：直接推进，记录在 memory 中待后续补充。
If no match found: proceed and note in memory for future.

---

### Step 3：文件生成 / File Generation

按以下顺序生成，**每文件严格专注一件事**：
Generate in order. **Each file has exactly one responsibility.**

```
SOUL.md         气质/价值观/风格         ≤150行
IDENTITY.md     角色定位/职责边界        ≤120行
USER.md         用户偏好/目标/禁区       ≤150行
TOOLS.md        工具规则/风险确认        ≤200行
AGENTS.md       启动顺序/工作协议        ≤500行
HEARTBEAT.md    轻量巡检清单            ≤50行
MEMORY.md       长期浓缩事实            20–50条
BOOTSTRAP.md    首次对话引导            ≤50行
memory/今日.md  当天初始化日志
```

**双语输出规则 / Bilingual Output Rule:**
- 所有文件生成**中英文两个版本**
- 中文版：`{filename}.md`（主文件，默认）
- 英文版：`{filename}.en.md`
- Generate **both Chinese and English versions** of every file
- Chinese: `{filename}.md` (primary, default)
- English: `{filename}.en.md`

**分层铁律 / Separation Rules（违反即返工 / violations require rework）：**

| 文件 | 只写什么 | 绝对不写什么 |
|------|---------|------------|
| SOUL.md | 人格/气质/价值观/风格 | 流程、工具、用户信息 |
| IDENTITY.md | 角色定位/场景/边界 | 性格、用户偏好、记忆 |
| USER.md | 用户偏好/目标/禁区 | agent性格、流程步骤 |
| TOOLS.md | 工具决策规则/风险等级 | 角色价值观、用户信息 |
| AGENTS.md | 启动顺序/调度协议 | 性格、工具细节、用户偏好 |
| HEARTBEAT.md | 轻量巡检清单 | 一切其他内容 |

---

### Step 4：打包输出 / Package Output

目录命名：`workspace-{英文代称}`
Directory name: `workspace-{English abbreviation}`

```
workspace-{代称}/
├── AGENTS.md          # + AGENTS.en.md
├── BOOTSTRAP.md       # + BOOTSTRAP.en.md
├── HEARTBEAT.md       # + HEARTBEAT.en.md
├── IDENTITY.md        # + IDENTITY.en.md
├── MEMORY.md          # + MEMORY.en.md
├── SOUL.md            # + SOUL.en.md
├── TOOLS.md           # + TOOLS.en.md
├── USER.md            # + USER.en.md
├── memory/
│   └── YYYY-MM-DD.md
└── skills/
    ├── find-skills/        ← 必须预装 / must be pre-installed
    │   ├── SKILL.md
    │   └── _meta.json
    └── {other-skills}/
        └── SKILL.md
```

---

## 质检清单 / Quality Checklist

生成完成后逐项检查：
Run before finalizing:

- [ ] SOUL.md 只有气质，无流程无工具 / Soul only, no process or tools
- [ ] IDENTITY.md 职责边界清晰，无用户信息 / Clear boundary, no user info
- [ ] USER.md 有待填写的占位符 / Has fill-in placeholders
- [ ] TOOLS.md 有三色风险等级表 / Has color-coded risk table
- [ ] AGENTS.md 启动顺序在第一段 / Boot sequence is first section
- [ ] HEARTBEAT.md ≤50行 / ≤50 lines
- [ ] find-skills 已预装到 skills/ / find-skills pre-installed
- [ ] 已执行 clawhub 技能查询 / clawhub query was run
- [ ] 中英文两版均已生成 / Both CN and EN versions generated
- [ ] 目录名以 workspace- 开头 / Directory starts with workspace-

---

## 示例角色映射 / Example Role Mapping

### PM（产品经理）
- 气质：极简、偏执、用户第一、直接
- 技能查询：`npx skills find product prd roadmap`
- 必装：docx, pptx

### DEV（工程师）
- 气质：精确、务实、先跑通再优化
- 技能查询：`npx skills find code review github testing`
- 必装：github, code-runner

### RESEARCHER（研究员）
- 气质：深挖、存疑、系统化、引用第一
- 技能查询：`npx skills find research web summarize pdf`
- 必装：web-research, pdf-reader
