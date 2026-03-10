# Setup Guide

How to connect this repo to your AI tools. Run these from the root of your cloned `ai-toolkit` repo.

## Claude Code

Claude Code looks for skills in `~/.claude/skills/` (personal) or `.claude/skills/` (per-project).

**Option A: Symlink the whole skills directory (recommended)**
```bash
# Linux/Mac
ln -s "$(pwd)/skills" ~/.claude/skills

# If ~/.claude/skills already exists and has other skills:
# Symlink individual skill folders instead
ln -s "$(pwd)/skills/leadership-report" ~/.claude/skills/leadership-report
ln -s "$(pwd)/skills/brag-doc-updater" ~/.claude/skills/brag-doc-updater
```

**Option B: Per-project CLAUDE.md**
Copy or symlink `system-prompts/claude-code.md` as `CLAUDE.md` in any project root where you want your preferences loaded.

## Claude Desktop (with Obsidian MCP)

If you keep this repo as a vault or subfolder within your Obsidian vault, Claude Desktop can access it through the Obsidian MCP. Otherwise, point the filesystem MCP at this repo's directory.

Skills aren't auto-triggered in Claude Desktop the way they are in Claude Code — you'd reference them manually ("use my leadership-report skill for this") or paste the SKILL.md content into context.

## claude.ai

Skills in claude.ai work through the web interface's skill upload feature. Upload the `.skill` files directly, or:
1. Copy the SKILL.md content
2. Use it as context in a conversation
3. Or install it via Settings if the feature is available in your plan

For system prompts: paste the content of `system-prompts/claude-ai.md` into Settings → Profile → User Preferences.

## GitHub Copilot

LEARNINGS.md is automatically picked up by Copilot when it's at the repo root. Since we keep it in `learnings/`, you have two options:

```bash
# Option A: Symlink to repo root (if using this repo as a project)
ln -s learnings/LEARNINGS.md ./LEARNINGS.md

# Option B: Copy to other project repos where you want Copilot to use it
cp learnings/LEARNINGS.md /path/to/your/project/LEARNINGS.md
```

For Copilot custom instructions: paste `system-prompts/copilot.md` into your Copilot settings.

## Keeping things in sync

The repo is the source of truth. The workflow is:
1. Edit files in the repo
2. Commit and push
3. On other machines: `git pull`
4. Symlinks update automatically; copied files need to be re-copied

If you change a system prompt in a tool's settings directly (e.g., editing claude.ai preferences in the UI), update the file in `system-prompts/` afterward so the repo stays current.
