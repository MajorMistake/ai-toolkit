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
User <-> ADK Web UI <-> Agent (Planner)
                            |
                  +---------+---------+
                  |         |         |
                Jira    Obsidian   Feedback
                Tools    Vault      Files
                  |
          [write gate: before_tool_callback]
          mode: local_only | confirm | live
```

### Key Design Decisions

- **One agent, not two.** Jira data wrangling is deterministic code (tools), not LLM reasoning. The agent only gets invoked for work that benefits from reasoning.
- **Manual sync, not bidirectional.** The agent drafts Jira comments; you review and approve before posting. Trust level matches automation level.
- **Markdown-first state.** All local state is plain markdown in an Obsidian vault -- grep-able, version-controllable, human-readable.
- **Feedback via files, not prompt engineering.** Corrections accumulate in a markdown file the agent reads at planning time. Preferences are curated manually. Both are fully inspectable.
- **Write operations are gated.** Jira write tools (`post_comment`, `update_ticket_status`, `create_subtask`) are enforced by a `before_tool_callback` that checks `JIRA_WRITE_MODE` and, in `confirm` mode, requires explicit user approval in the chat before executing.

## Setup

```bash
# Clone and install
cd pm-agent
poetry env use python3   # if `python` isn't on your PATH
poetry install

# Configure
cp .env.example .env
# Edit .env with your project ID and Jira credentials

# Copy vault template to your Obsidian vault
cp -r vault_template/pm-agent ~/your-obsidian-vault/pm-agent
# Update VAULT_PATH in .env

# Run locally with ADK dev UI
poetry run adk web
```

## Configuration

All configuration is via environment variables (loaded from `.env`).

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` | `cyderes-test` | GCP project for VertexAI |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | VertexAI region |
| `USE_MOCK_JIRA` | `true` | Use mock data instead of real Jira API |
| `JIRA_WRITE_MODE` | `local_only` | Write gate mode (see below) |
| `VAULT_PATH` | `~/obsidian-vault/pm-agent` | Obsidian vault root |
| `COST_LOG_PATH` | `~/.pm-agent/cost_log.jsonl` | JSONL cost log location |
| `AGENT_LABEL` | `pm-agent` | Label for cost attribution |

### Write Modes (`JIRA_WRITE_MODE`)

| Mode | Behavior |
|------|----------|
| `local_only` | Jira write tools are always blocked. Agent drafts content into vault markdown files instead. Use this for development and testing. |
| `confirm` | Two-phase flow: agent presents drafted content, waits for user approval (e.g. "yes", "go ahead", "lgtm"), then executes. Approval is checked via word-boundary matching on the user's last message -- the model cannot self-approve. |
| `live` | Write tools execute immediately with no gate. Only use this after significant reliability validation. |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Root log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FORMAT` | *(console)* | Set to `json` for JSON lines output |

Logging uses [structlog](https://www.structlog.org/) with structured key-value events. In dev mode (default), output is colorized and human-readable on stderr. Set `LOG_FORMAT=json` for machine-parseable JSON lines.

All log events from the agent, tools, cost tracker, and third-party libraries (ADK, google-genai) flow through the same structlog processors.

Key log events:

| Event | Level | Source | Description |
|-------|-------|--------|-------------|
| `agent_initialized` | info | agent.py | Startup config summary (model, write mode, mock status, tool count) |
| `llm_call_logged` | info | cost_tracker.py | Every LLM call with model, tokens, cost, latency |
| `write_gate_blocked` | info | agent.py | Write tool blocked by write mode or pending approval |
| `write_gate_approved` | info | agent.py | Write tool approved by user |
| `tool_write` | info | jira_tools.py | Jira write operation executed |
| `sprint_setup` | info | local_state_tools.py | New sprint directory created |
| `ticket_notes_written` | info | local_state_tools.py | Ticket notes written to vault |
| `correction_recorded` | info | feedback_tools.py | User correction logged |

### GCP Cost Labels

Every Vertex AI API call includes labels for cost attribution in GCP billing:

```
cy_dept: engineering
cy_dept_group: analytics
cy_project: pm_agent
cy_env_type: testing
agent: pm-agent
```

These labels are defined in `config/settings.py` (`VERTEX_LABELS`) and applied in two places:
- `GenerateContentConfig.labels` on the Agent (sent to Vertex AI API)
- `billing_labels` in the local JSONL cost log

## Project Structure

```
pm-agent/
├── agents/planner/
│   ├── agent.py              # Agent definition, write gate callback
│   ├── __init__.py            # Exports root_agent for ADK discovery
│   └── prompts/
│       └── system_prompt.md   # Agent instructions
├── tools/
│   ├── __init__.py            # Aggregates ALL_TOOLS
│   ├── jira_tools.py          # Jira read/write tools (7 tools)
│   ├── jira_mock_data.py      # Mock sprint + ticket data
│   ├── local_state_tools.py   # Obsidian vault operations (9 tools)
│   └── feedback_tools.py      # Preferences + corrections (2 tools)
├── monitoring/
│   └── cost_tracker.py        # JSONL cost logging + ADK callbacks
├── config/
│   ├── settings.py            # Pydantic settings, VERTEX_LABELS, logging init
│   └── logging.py             # Structlog configuration
├── vault_template/            # Template for Obsidian vault structure
├── tests/
│   └── test_core.py           # 50 tests covering all modules
├── pyproject.toml
└── .env.example
```

## Build Sequence

- [x] 1. Monitoring/cost tracking scaffold
- [x] 2. Mock Jira tools
- [x] 3. Local state tools + vault structure
- [x] 4. Planner agent with system prompt
- [x] 5. Write gate with JIRA_WRITE_MODE enforcement
- [x] 6. GCP cost labels on Vertex AI API calls
- [x] 7. Structlog integration across all modules
- [ ] 8. Comment drafting workflow
- [ ] 9. Brag doc integration
- [ ] 10. Real Jira integration (swap mocks for live API)
- [ ] 11. Hardening (input validation, error handling, edge cases)

## Usage Workflows

**Sprint start:** "Pull my tickets for this sprint" -> agent fetches, creates local note files, suggests breakdown and sequencing

**Daily work:** Write rough notes in ticket files, ask agent to draft Jira comments when needed

**Sprint end:** "Generate brag doc entries for this sprint" -> agent reviews tickets + notes, produces STAR-format entries

**Ad hoc:** "Help me break down DATA-3401" or "What's blocking me?"

## Cost Monitoring

All LLM calls are logged to `~/.pm-agent/cost_log.jsonl` with:
- Model, token counts (input/output/thinking/cached), latency
- Workflow type and ticket context
- Billing labels matching GCP Vertex AI labels
- Estimated USD cost (based on published Vertex AI pricing)

The cost tracker also emits structured log events via structlog, so cost data appears in both the JSONL file and the application log stream.

## Running Tests

```bash
poetry run pytest tests/ -v
```

50 tests covering: Pydantic model validation, cost estimation, cost tracker JSONL output, ADK callback simulation, write gate enforcement across all three modes, approval phrase word-boundary matching, Jira mock tools, vault operations, and feedback tools.
