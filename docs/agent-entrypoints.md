# Agent Entrypoints

## Purpose

This is the canonical mapping between agent families and their startup / skill-like files in this repository.

## Codex / OpenAI-Style Agents

Startup file:

- [AGENTS.md](../AGENTS.md)

Skill-like files:

- `skills/*/SKILL.md`

## Claude Code

Startup file:

- [CLAUDE.md](../CLAUDE.md)

Skill-like files:

- `.claude/agents/*.md`
- `.claude/commands/*.md`

## Gemini CLI

Startup file:

- [GEMINI.md](../GEMINI.md)

Skill-like files:

- `gemini-skills/*.md`

## Design Rule

Agent-family-specific entry files should stay thin.

Shared operational truth should live in:

- [AGENTS.md](../AGENTS.md)
- [learning-system-v4.md](../docs/learning-system-v4.md)
- [external-ai-operating-guide.md](../docs/external-ai-operating-guide.md)
- [agent-operating-contract.md](../docs/agent-operating-contract.md)
- [artifact-catalog.md](../docs/artifact-catalog.md)
- [memory-model.md](../docs/memory-model.md)
