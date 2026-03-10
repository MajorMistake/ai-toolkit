# System Prompts

Custom instructions for different AI tools. Each file is the source-of-truth for that tool's configuration — edit here first, then paste into the tool's settings.

## Index

| File | Tool | Where to paste |
|------|------|---------------|
| `claude-ai.md` | claude.ai | Settings → Profile → User Preferences |
| `claude-code.md` | Claude Code | Project root as `CLAUDE.md` |
| `copilot.md` | GitHub Copilot | Copilot settings → Custom instructions |

## Why version control these?

- Track how your preferences evolve over time
- Diff what you tell different tools (inconsistencies = bugs)
- Recover easily when switching machines or resetting tools
- Share subsets with others without exposing everything
