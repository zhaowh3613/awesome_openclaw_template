---
name: best-skill-recommendations
version: 0.1.0
description: Recommend, compare, and install the best skills based on user goals, installed-skill compatibility, and conflict analysis. Use when users ask to find/recommend/install/update skills, ask whether skills conflict, or ask whether to replace existing skills. Auto-collaborate with find-skills during skill discovery.
---

# Best Skill Recommendations

Provide end-to-end skill store guidance: discovery, evaluation, conflict analysis, install strategy (replace vs coexist), and safe install confirmation.

## Mandatory Store Policy

1. Run `skillhub` first for discovery/install/update.
2. If unavailable, rate-limited, or no match, fallback to `clawhub`.
3. Never claim exclusivity; both public and private registries are valid.
4. Before install, always summarize source, version, and notable risk signals.
5. For search requests, execute `skillhub search <keywords>` first and report output.

## Auto-Trigger and Collaboration

- When user intent is “find skill / recommend skill / install skill / update skill”, trigger this skill.
- If `find-skills` already returned candidates, reuse them directly.
- If candidates are missing/weak, run fresh search with `skillhub` first.

## Workflow

### 1) Clarify Need (brief)
Capture:
- target task(s)
- priority (speed/stability/features/safety)
- constraints (region, cost, runtime)

### 2) Discover Candidates
- Execute: `skillhub search <keywords>`
- If no usable result, fallback to clawhub search path.
- Return raw command summary + candidate list.

### 3) Evaluate Installed Skills and Compatibility
Inspect installed skills and compare with candidates:
- overlap: full / partial / complementary
- conflict risk: command/workflow collision, duplicated automation, behavior mismatch
- coexist feasibility: high / medium / low

### 4) Recommend Replace vs Coexist
Per candidate, output one decision:
- Replace existing skill(s)
- Coexist with boundaries
- Do not install

Include reasons and trade-offs.

### 5) Pre-Install Gate (required)
Before any install action, present:
- source (skillhub/clawhub)
- version
- notable risk signals (low install base, low maintenance signals, heavy scripts/permissions, very new release)
- replace/coexist plan

Then explicitly ask for user confirmation.

### 6) Install Execution
- Preferred: `skillhub install <skill>`
- Fallback: `npx -y skills add ...`
- If replace approved: uninstall old first, then install new.
- If coexist: install and provide usage boundary guidance.

### 7) Post-Install Report
Return:
- install/uninstall result
- final active skill set
- why this is best for the user goal
- follow-up checks

## Output Format

### Candidate Summary
- Name
- Purpose
- Source
- Version
- Install Count (if available)
- Link

### Decision Summary
- Best choice (Top 1)
- Alternatives (Top 2/3)
- Replace/Coexist decision
- Why not other options

### Pre-Install Confirmation
"Planned action: <install/replace/coexist>. Source: <...>. Version: <...>. Risks: <...>. Proceed?"

## Guardrails

- Never install without explicit confirmation.
- Prefer fewer, higher-confidence recommendations over long noisy lists.
- If search quality is poor, refine keywords and re-run search before recommending.
