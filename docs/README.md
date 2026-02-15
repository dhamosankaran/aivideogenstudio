# AIVideoGen Documentation

> **Single source of truth for all project documentation**

## 📁 Directory Structure

```
docs/
├── README.md              # This file
├── learning.md            # Lessons learned (update after each session)
│
├── ai-rules/              # AI assistant instructions
│   ├── AGENTS.md          # CTO persona & behaviors
│   ├── CODING_STANDARDS.md # Code conventions
│   └── CONTEXT.md         # Project context & architecture
│
├── workflows/             # Slash command definitions
│   ├── create-issue.md    # /create-issue - Quick idea capture
│   ├── exploration.md     # /exploration - Discovery (NO CODE)
│   ├── create-plan.md     # /create-plan - Implementation blueprint
│   ├── execute.md         # /execute - Write code
│   ├── review.md          # /review - Self code review
│   ├── peer-review.md     # /peer-review - Multi-model review
│   ├── learning.md        # /learning - 80/20 concepts
│   └── postmortem.md      # /postmortem - Fix mistakes
│
├── explorations/          # Discovery phase documents
│   ├── mvp-definition.md
│   ├── future-features-exploration.md
│   └── ...
│
└── issues/                # Captured ideas & issues
    ├── README.md          # Issues index
    └── ISSUE-YYYY-MM-DD-*.md
```

## 🔗 Quick Links

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | **Primary AI instructions** (read first!) |
| [ROADMAP.md](../ROADMAP.md) | Product phases & timeline |
| [SESSION_HANDOFF.md](../SESSION_HANDOFF.md) | Current state & quick start |
| [learning.md](./learning.md) | Mistakes & prevention |
| [issues/README.md](./issues/README.md) | Issues index |

## 🎯 AI Assistant Rules

**Always read before making decisions:**

1. **[CLAUDE.md](../CLAUDE.md)** - Session checklist, doc locations, CTO persona
2. **[ai-rules/AGENTS.md](./ai-rules/AGENTS.md)** - Detailed behaviors, anti-patterns
3. **[ai-rules/CODING_STANDARDS.md](./ai-rules/CODING_STANDARDS.md)** - Code conventions
4. **[ai-rules/CONTEXT.md](./ai-rules/CONTEXT.md)** - Architecture, tech stack

## 📋 Workflow Commands

| Command | When to Use |
|---------|-------------|
| `/create-issue` | Quick idea capture (don't break flow) |
| `/exploration` | Understand problem before coding (NO CODE) |
| `/create-plan` | Create implementation blueprint |
| `/execute` | Write code following approved plan |
| `/review` | Self-review before peer review |
| `/postmortem` | Learn from mistakes |

## ⚠️ Important Notes

1. **CLAUDE.md is source of truth** - Other tool configs reference it
2. **Update learning.md** - After every session with mistakes/learnings
3. **Check SESSION_HANDOFF.md** - Before starting any work
4. **Validate .env** - API keys match default providers

---

**Last Updated**: 2026-02-07
