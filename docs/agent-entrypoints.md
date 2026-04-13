# Agent Entrypoints

## Purpose

This is the canonical mapping between agent families and their startup / skill-like files in this repository.

## Codex / OpenAI-Style Agents

Startup file:

- [AGENTS.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/AGENTS.md)

Skill-like files:

- `skills/*/SKILL.md`

## Claude Code

Startup file:

- [CLAUDE.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/CLAUDE.md)

Skill-like files:

- `.claude/agents/*.md`
- `.claude/commands/*.md`

## Gemini CLI

Startup file:

- [GEMINI.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/GEMINI.md)

Skill-like files:

- `gemini-skills/*.md`

## Design Rule

Agent-family-specific entry files should stay thin.

Shared operational truth should live in:

- [AGENTS.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/AGENTS.md)
- [external-ai-operating-guide.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/external-ai-operating-guide.md)
- [agent-operating-contract.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/agent-operating-contract.md)
- [artifact-catalog.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/artifact-catalog.md)
- [memory-model.md](/Users/idonghun/IdeaProjects/woowa-mission-coach/docs/memory-model.md)
