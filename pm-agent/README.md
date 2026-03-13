# PM Agent

Personal Jira PM agent built on Google ADK + VertexAI. Compensates for executive function challenges by providing structured task breakdown, sprint planning, comment drafting, and brag doc generation.

## Why This Exists

This serves two purposes:
1. **Direct productivity tool** -- structured sprint planning, task breakdown, and progress tracking that works alongside (not inside) Jira
2. **Learning investment** -- hands-on experience building agentic workflows on VertexAI/ADK for professional development

**Cost justification:** Estimated <$20/month in API spend. Even modest time savings at engineering labor rates provide positive ROI. All calls are labeled and logged for full cost attribution.

## Architecture

Single Planner agent (Gemini Flash) with three tool categories:

- **Jira tools** -- read/write operations against Jira REST API (currently mocked)
- **Local state tools** -- Obsidian vault operations for private notes, sprint tracking, brag doc
- **Feedback tools** -- lightweight learning loop via preferences + corrections files

```
User <-> ADK Agent (Planner)
              |
    +---------+---------+
    |         |         |
  Jira    Obsidian   Feedback
  Tools    Vault      Files
```

### Key Design Decisions

- **One agent, not two.** Jira data wrangling is deterministic code (tools), not LLM reasoning. The agent only gets invoked for work that benefits from reasoning.
- **Manual sync, not bidirectional.** The agent drafts Jira comments; you review and approve before posting. Trust level matches automation level.
- **Markdown-first state.** All local state is plain markdown in an Obsidian vault -- grep-able, version-controllable, human-readable.
- **Feedback via files, not prompt engineering.** Corrections accumulate in a markdown file the agent reads at planning time. Preferences are curated manually. Both are fully inspectable.

## Setup

```bash
# Clone and install
cd pm-agent
poetry install

# Configure
cp .env.example .env
# Edit .env with your project ID and Jira credentials

# Copy vault template to your Obsidian vault
cp -r vault_template/pm-agent ~/your-obsidian-vault/pm-agent
# Update VAULT_PATH in .env

# Run locally with ADK dev UI
cd agents/planner
poetry run adk web
```

## Project Structure

```
pm-agent/
├── agents/planner/          # ADK agent definition + system prompt
├── tools/                   # Jira, local state, and feedback tools
├── monitoring/              # Cost tracking and observability
├── config/                  # Central configuration
├── vault_template/          # Template for Obsidian vault structure
└── tests/                   # Smoke tests for all modules
```

## Build Sequence

- [x] 1. Monitoring/cost tracking scaffold
- [x] 2. Mock Jira tools
- [x] 3. Local state tools + vault structure
- [x] 4. Planner agent with system prompt
- [ ] 5. Comment drafting workflow
- [ ] 6. Brag doc integration
- [ ] 7. Real Jira integration (swap mocks for live API + HITL confirmation)
- [ ] 8. Hardening (input validation, error handling, edge cases)

## Usage Workflows

**Sprint start:** "Pull my tickets for this sprint" -> agent fetches, creates local note files, suggests breakdown and sequencing

**Daily work:** Write rough notes in ticket files, ask agent to draft Jira comments when needed

**Sprint end:** "Generate brag doc entries for this sprint" -> agent reviews tickets + notes, produces STAR-format entries

**Ad hoc:** "Help me break down DATA-3401" or "What's blocking me?"

## Cost Monitoring

All LLM calls are logged to `~/.pm-agent/cost_log.jsonl` with:
- Model, token counts, latency
- Workflow type and ticket context
- Billing labels for GCP cost attribution
- Estimated USD cost

Cost summary CLI command is planned for a future release.
