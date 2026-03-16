# AIVideoGen Documentation

> Single source of truth for project documentation.

## Quick Links

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | **Primary AI instructions** — read first |
| [SESSION_HANDOFF.md](../SESSION_HANDOFF.md) | Current state & what's next |
| [ROADMAP.md](../ROADMAP.md) | Product phases & priorities |
| [docs/learning.md](./learning.md) | Lessons learned — mistakes & fixes |
| [docs/issues/README.md](./issues/README.md) | Issues index |

## Directory Structure

```
docs/
├── README.md              # This file
├── learning.md            # Lessons learned (update each session)
│
├── ai-rules/              # AI assistant instructions
│   └── CTO.md             # CTO persona, behavioral rules, modes
│
├── explorations/          # Discovery docs (one per feature/decision)
│
├── configuration/         # How-to guides for specific systems
│   └── end-screen-guide.md
│
└── issues/                # Captured ideas & feature requests
    ├── README.md           # Issues index
    └── ISSUE-YYYY-MM-DD-*.md
```

## .claude/ (Claude Code Specific)

```
.claude/
├── rules/                 # Auto-injected into every session
│   ├── architecture.md    # Content-type routing, pipeline, digest pattern
│   ├── backend.md         # Python naming, error handling, FastAPI
│   └── frontend.md        # React conventions, CSS design system tokens
└── skills/                # Slash command definitions
    ├── exploration/        # /exploration — discovery phase (NO CODE)
    ├── create-issue/       # /create-issue — capture ideas
    ├── create-plan/        # /create-plan — implementation blueprint
    ├── execute/            # /execute — write code
    ├── review/             # /review — self code review
    ├── peer-review/        # /peer-review — multi-model synthesis
    ├── learning/           # /learning — 80/20 concepts
    └── postmortem/         # /postmortem — root cause analysis
```

## Workflow Commands

| Command | Phase | Rule |
|---------|-------|------|
| `/exploration` | Discovery | NO CODE — understand problem first |
| `/create-issue` | Capture | Log scope creep without breaking flow |
| `/create-plan` | Planning | Must be approved before `/execute` |
| `/execute` | Building | Only after approved plan |
| `/review` | Quality | Self-review before peer review |
| `/peer-review` | Quality | Multi-model synthesis |
| `/learning` | Growth | 80/20 concept explanation |
| `/postmortem` | Improvement | Root cause + prevention |
