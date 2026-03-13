"""Planner agent definition using Google ADK.

This is the single agent for the PM system. It has access to:
- Jira tools (read/write, currently mocked)
- Local state tools (Obsidian vault operations)
- Feedback tools (learning from corrections)

The agent uses Gemini Flash by default for cost efficiency.
Switch to gemini-2.5-pro for complex planning sessions if needed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import structlog
from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig

from config.settings import settings, VERTEX_LABELS
from monitoring.cost_tracker import CostTracker
from tools import ALL_TOOLS

logger = structlog.get_logger(__name__)

# Load system prompt from markdown file
_PROMPT_DIR = Path(__file__).parent / "prompts"
_SYSTEM_PROMPT = (_PROMPT_DIR / "system_prompt.md").read_text()

# Cost tracker -- logs every LLM call to JSONL with real usage metadata
_tracker = CostTracker(settings.monitoring)

# Combine shared Vertex labels with the per-agent label for the API config.
_API_LABELS = {**VERTEX_LABELS, "agent": settings.monitoring.agent_label}

# Tools that modify external state -- require user confirmation via ADK UI.
_WRITE_TOOLS = {"post_comment", "update_ticket_status", "create_subtask"}

# Phrases in the user's most recent message that count as approval.
# Matched with word boundaries to avoid false positives (e.g. "yesterday").
_APPROVAL_PHRASES = [
    "approve", "approved", "yes", "go ahead", "do it", "post it",
    "lgtm", "ship it", "confirmed", "proceed", "ok post", "yes post",
]
_APPROVAL_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(p) for p in _APPROVAL_PHRASES) + r")\b",
    re.IGNORECASE,
)


def _get_last_user_text(tool_context: Any) -> str | None:
    """Extract the text of the most recent user message from the ADK session."""
    session = getattr(tool_context, "session", None)
    if not session:
        return None
    events = getattr(session, "events", None)
    if not events:
        return None

    for event in reversed(events):
        if getattr(event, "author", None) != "user":
            continue
        content = getattr(event, "content", None)
        if not content:
            return None
        parts = getattr(content, "parts", None)
        if not parts:
            return None
        return " ".join(
            getattr(p, "text", "") for p in parts if getattr(p, "text", None)
        ).strip()

    return None


def _user_approved(tool_context: Any) -> bool:
    """Check if the user's most recent message contains an approval phrase.

    Uses word-boundary regex so that e.g. "yes" doesn't match "yesterday".
    This keeps the approval gate outside the model's control.
    """
    text = _get_last_user_text(tool_context)
    if not text:
        return False
    return bool(_APPROVAL_RE.search(text))


async def _confirm_before_write(
    *, tool: Any, args: dict[str, Any], tool_context: Any
) -> dict[str, Any] | None:
    """ADK before_tool_callback -- gates write operations based on JIRA_WRITE_MODE.

    Modes:
      - local_only: always block Jira writes (drafts go to vault instead)
      - confirm:    two-phase flow -- block, present draft, allow after user approval
      - live:       pass through (no gate)

    Returns None to allow the tool call to proceed.
    Returns a dict to block execution (used as the tool result instead).
    """
    tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", "unknown")
    if tool_name not in _WRITE_TOOLS:
        return None

    write_mode = settings.jira.write_mode

    if write_mode == "live":
        logger.info("write_gate_passed", tool=tool_name, write_mode="live")
        return None

    if write_mode == "local_only":
        logger.info("write_gate_blocked", tool=tool_name, write_mode="local_only")
        return {
            "status": "blocked",
            "reason": (
                f"Tool '{tool_name}' is disabled (JIRA_WRITE_MODE=local_only). "
                "Save the drafted content to the ticket notes in the vault instead "
                "using write_ticket_notes."
            ),
        }

    # write_mode == "confirm": two-phase approval flow
    if _user_approved(tool_context):
        logger.info("write_gate_approved", tool=tool_name, write_mode="confirm")
        return None

    logger.info("write_gate_blocked", tool=tool_name, write_mode="confirm", reason="awaiting_user_approval")
    return {
        "status": "blocked",
        "reason": (
            f"Tool '{tool_name}' is a write operation. "
            "Present the drafted content to the user for review. "
            "If they approve, you may retry on the next turn. "
            "If they deny or give feedback, incorporate it and draft again."
        ),
    }


# --- Agent definition ---
# This is the root_agent that ADK discovers.

root_agent = Agent(
    model="gemini-2.5-flash",
    name="pm_planner",
    description=(
        "Personal PM assistant that helps break down Jira tickets, "
        "manage sprint work, draft comments, and maintain a brag doc. "
        "Works with both Jira data and local Obsidian vault notes."
    ),
    instruction=_SYSTEM_PROMPT,
    tools=ALL_TOOLS,
    generate_content_config=GenerateContentConfig(labels=_API_LABELS),
    before_tool_callback=_confirm_before_write,
    before_model_callback=_tracker.before_model_callback,
    after_model_callback=_tracker.after_model_callback,
)

logger.info(
    "agent_initialized",
    agent=root_agent.name,
    model="gemini-2.5-flash",
    write_mode=settings.jira.write_mode,
    use_mock=settings.jira.use_mock,
    vault_path=str(settings.vault.root),
    tool_count=len(ALL_TOOLS),
)
