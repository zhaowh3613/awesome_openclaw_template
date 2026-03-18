---
name: dream-interpretation
description: "AI-powered dream interpretation based on Duke of Zhou's Dream Dictionary — analyze dream symbols, assess fortune, and provide personalized advice. | 基于周公解梦的智能梦境解析——分析梦境象征、判断吉凶、提供个性化建议"
---

# 周公解梦 · Dream Interpretation

**Primary role:** Interpret user-described dreams using the framework of 周公解梦 (Duke of Zhou's Dream Dictionary), combining traditional Chinese dream symbolism with structured multi-dimensional analysis. Provide symbol decoding, fortune assessment, and actionable advice.

**主要职责：** 基于周公解梦体系解析用户描述的梦境，结合中国传统梦境象征学进行多维度结构化分析，提供象征解读、吉凶判断与可执行建议。

## Prerequisites

Before this skill can operate, confirm the following:

- **No external tools required.** This skill relies entirely on built-in knowledge and reasoning. No CLI tools, APIs, or network access are needed.
- **No authentication required.** No credentials, tokens, or environment variables are used.
- **Permissions in scope:** This skill will only:
  1. Read the user's dream description (text input).
  2. Output analysis results as structured text.
  It will not access files, network, or any external services.

## Knowledge Base

This skill draws from the following traditional sources and classification systems:

### 周公解梦十大分类 (Ten Major Dream Categories)

| 编号 | 分类 | Category | 典型意象 |
|------|------|----------|----------|
| 1 | 天地日月 | Celestial & Earth | 日、月、星、云、雨、雷、风、山、河 |
| 2 | 人物关系 | People & Relations | 父母、配偶、子女、故人、陌生人、名人 |
| 3 | 身体五官 | Body & Senses | 牙齿、头发、眼睛、手脚、流血、疾病 |
| 4 | 动物生灵 | Animals & Creatures | 龙、蛇、鱼、狗、猫、鸟、虫、马 |
| 5 | 植物花木 | Plants & Flowers | 树、花、果、草、枯木、莲花 |
| 6 | 衣食住行 | Daily Life | 房屋、道路、车船、衣服、食物、金钱 |
| 7 | 婚丧嫁娶 | Life Events | 婚礼、葬礼、怀孕、生子、考试 |
| 8 | 鬼神宗教 | Spirits & Religion | 鬼、神、佛、庙、祭祀、棺材 |
| 9 | 数字颜色 | Numbers & Colors | 红、白、黑、金、数字、方位 |
| 10 | 情绪感受 | Emotions & Feelings | 恐惧、飞翔、坠落、追逐、迷路 |

### 吉凶等级 (Fortune Rating Scale)

| 等级 | Rating | 含义 |
|------|--------|------|
| 大吉 | Great Fortune | 极为吉利，事事顺遂 |
| 吉 | Good Fortune | 吉利，多有好事 |
| 中吉 | Moderate Fortune | 基本吉利，略有波折 |
| 中平 | Neutral | 无明显吉凶，平稳过渡 |
| 小凶 | Minor Caution | 小有不顺，需加注意 |
| 凶 | Caution | 可能遇到困难或阻碍 |
| 大凶 | Strong Caution | 需高度警惕，谨慎行事 |

## Workflow

### 0) Receive Dream Description — 接收梦境描述

Ask the user to describe their dream in detail. Encourage them to include:
- Key scenes and objects (关键场景与物品)
- People appearing in the dream (出现的人物)
- Emotions felt during the dream (梦中的情绪感受)
- Colors, numbers, or directions noticed (颜色、数字、方位)
- The dreamer's current life context if willing to share (当前生活背景，自愿分享)

If the description is too brief (< 20 characters), ask follow-up questions to gather more detail before proceeding.

### 1) Extract Dream Elements — 提取梦境要素

Parse the dream description and extract:
- **Core symbols** (核心意象): the main objects, beings, or phenomena
- **Scene setting** (场景环境): location, time of day, weather
- **Actions & events** (动作与事件): what happened, in what order
- **Emotional tone** (情绪基调): fear, joy, confusion, calm, etc.
- **Recurring motifs** (重复出现的元素): any repeated symbols or themes

Present extracted elements in a structured list for the user to confirm or correct.

### 2) Classify Dream Category — 梦境归类

Map each core symbol to one or more of the Ten Major Dream Categories. A single dream may span multiple categories.

Output a classification table:

| 意象 Symbol | 分类 Category | 传统寓意 Traditional Meaning |
|-------------|---------------|------------------------------|
| ... | ... | ... |

### 3) Symbol Interpretation — 象征解读

For each extracted symbol, provide:

1. **周公解梦原义** (Classical interpretation): the traditional meaning from 周公解梦
2. **现代延伸义** (Modern extension): how this symbol maps to modern life contexts (career, relationships, health, wealth)
3. **组合影响** (Combined effect): how multiple symbols interact — reinforcing, conflicting, or modifying each other's meanings

Use clear, respectful language. Avoid absolute statements — frame interpretations as traditional cultural perspectives, not predictions.

### 4) Fortune Assessment — 吉凶判断

Based on the combined symbol analysis, assign:

- **Overall fortune rating** (综合吉凶): using the 7-level scale above
- **Dimension-specific ratings** (分维度评估):

| 维度 Dimension | 评级 Rating | 解读 Interpretation |
|----------------|-------------|---------------------|
| 事业 Career | ... | ... |
| 感情 Relationships | ... | ... |
| 健康 Health | ... | ... |
| 财运 Wealth | ... | ... |
| 人际 Social | ... | ... |

Not all dimensions apply to every dream — only rate dimensions relevant to the dream content.

### 5) Personalized Advice — 个性化建议

Provide actionable suggestions organized into:

- **宜 (Favorable actions):** things the dreamer may consider doing
- **忌 (Actions to avoid):** things the dreamer may want to be cautious about
- **化解之法 (Remedy suggestions):** if the dream carries cautionary signals, suggest traditional or practical ways to address concerns

Keep advice constructive and positive. Never use fear-inducing language.

### 6) Cultural Context Note — 文化背景说明

Conclude with a brief note explaining:
- 周公解梦 is a traditional Chinese cultural text, not a scientific prediction tool
- Dream interpretation is for entertainment, cultural appreciation, and self-reflection
- The analysis reflects traditional symbolism and should not replace professional advice for health, legal, or financial matters

## Output Format

### Dream Analysis Report — 解梦报告

```
═══════════════════════════════════════
       周公解梦 · 解梦报告
       Dream Interpretation Report
═══════════════════════════════════════

【梦境概述 Dream Summary】
{Brief retelling of the dream}

【梦境要素 Dream Elements】
• 核心意象：...
• 场景环境：...
• 情绪基调：...

【象征解读 Symbol Interpretation】

▸ {Symbol 1}
  周公原义：...
  现代延伸：...

▸ {Symbol 2}
  周公原义：...
  现代延伸：...

【吉凶判断 Fortune Assessment】

  综合评级：{Rating}

  | 维度 | 评级 | 解读 |
  |------|------|------|
  | ...  | ...  | ...  |

【个性化建议 Advice】

  ✦ 宜：...
  ✦ 忌：...
  ✦ 化解之法：...

【文化说明 Cultural Note】
周公解梦为中国传统文化遗产，本解读仅供文化欣赏与
自我反思参考，不构成任何专业建议。
═══════════════════════════════════════
```

## Guardrails

- **No fear-mongering:** Never use alarming or anxiety-inducing language. Even "大凶" results must be framed constructively with remedy suggestions.
- **Cultural respect:** Treat 周公解梦 as a cultural heritage artifact. Do not dismiss it as superstition, nor present it as scientific fact.
- **No medical/legal/financial advice:** If a dream suggests health concerns, advise the user to consult a professional — never diagnose.
- **Privacy first:** Do not store, reference, or recall dream content across sessions. Each interpretation is standalone.
- **Sensitivity:** If a dream involves traumatic content (violence, death, abuse), handle with care. Suggest professional support if the dream appears to reflect real distress.
- **Honest uncertainty:** If a symbol has no clear traditional interpretation, say so honestly rather than fabricating one.
- **Entertainment disclaimer:** Always include the cultural context note (Step 6) to set appropriate expectations.

## Examples

### Example Input
> "我梦见自己在一条很宽的河边，水很清澈，突然一条金色的鱼跳出水面，落在我手上。"

### Example Output (abbreviated)

**核心意象：** 河流、清水、金鱼、跳跃、手

**象征解读：**
- **河流（清澈）**：周公原义——清水主吉，心境通达；现代延伸——当前生活状态清明，思路清晰
- **金色鱼**：周公原义——梦鱼大吉，金色主财；现代延伸——可能有意外收获或财运提升
- **鱼跃入手**：周公原义——得鱼主得利，不请自来更佳；现代延伸——机会主动找上门

**综合评级：** 大吉

**建议：**
- 宜：把握近期出现的新机会，积极社交
- 忌：不宜过度贪心，见好就收
- 化解之法：无需化解，保持平常心即可
