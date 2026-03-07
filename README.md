# Awesome OpenClaw Templates

A curated collection of useful configurations and agent templates for [OpenClaw](https://github.com/anthropics/openclaw).

## Templates

### Multi-Agent: Discord Integration

**File:** [`multi_agents/discord_multi _agents.json`](multi_agents/discord_multi%20_agents.json)

A clean multi-agent template that sets up two collaborative agents on Discord:

| Agent      | ID                        | Model                    |
|------------|---------------------------|--------------------------|
| Coder      | `discord-agent-coder`     | `openai-codex/gpt-5.3-codex` |
| Reviewer   | `discord-agent-reviewer`  | `openai-codex/gpt-5.3-codex` |

#### How It Works

- **Agents** — Each agent has a unique ID, dedicated workspace, and assigned model.
- **Bindings** — Each agent is bound to a specific Discord account and channel, routing messages to the correct agent.
- **Channels** — Discord channels use an `allowlist` policy to control access, with streaming enabled for real-time interaction.

#### Quick Start

1. Copy the template and replace the placeholder values:
   - `<discord-bot-coder-token>` — Bot token for the coder agent
   - `<discord-bot-reviewer-token>` — Bot token for the reviewer agent
   - `<discord-server-id>` — Your Discord server (guild) ID
   - `<coder-bot-channel-id>` — Channel ID for the coder bot
   - `<reviewer-bot-channel-id>` — Channel ID for the reviewer bot
2. Place the config in your OpenClaw configuration directory.
3. Start OpenClaw — both agents will connect to their respective Discord channels.

## Contributing

Feel free to submit PRs with new templates or improvements to existing ones.
