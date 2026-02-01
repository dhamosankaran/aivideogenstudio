# AI Instructions for AIVideoGen Project

> **This directory contains AI-specific instructions and context that help AI assistants work effectively on this project.**

## Files in This Directory

| File | Purpose | Read By |
|------|---------|---------|
| `AGENTS.md` | Role definitions, personas, workflow overview | All AI tools |
| `CONTEXT.md` | Project context, architecture, decisions | All AI tools |
| `CODING_STANDARDS.md` | Code style, patterns, conventions | Code generation |

## How These Files Are Used

Different AI tools look for instructions in different places:

| Tool | Primary File | Also Reads |
|------|--------------|------------|
| **Claude (Anthropic)** | `/CLAUDE.md` | `.ai/AGENTS.md` |
| **Cursor** | `.cursorrules` | `.ai/CONTEXT.md` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | - |
| **Windsurf/Codeium** | `.windsurfrules` | - |
| **Aider** | `.aider.conf.yml` | - |
| **Generic** | `.ai/AGENTS.md` | All `.ai/*.md` |

## Keeping Instructions in Sync

The `CLAUDE.md` file in project root is the **source of truth**. Other tool-specific files should reference or mirror it.
