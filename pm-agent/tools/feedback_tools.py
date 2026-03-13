"""Feedback tools for agent learning.

Implements a lightweight feedback loop where corrections and preferences
are stored as markdown files in the vault. The agent reads these at the
start of planning sessions to calibrate its outputs.

Architecture:
    preferences.md  - Stable preferences and patterns (manually curated)
    corrections.md  - Append-only log of corrections during use

The agent has two tools:
    - get_feedback_context: reads both files to load into context
    - record_correction: appends a correction when the user says "no, do it this way"

Over time, the user can promote recurring corrections into preferences.md
and archive stale corrections. This keeps the feedback loop lightweight
and fully inspectable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from config.settings import settings


def get_feedback_context() -> dict:
    """Load preferences and recent corrections to calibrate planning.

    Call this at the start of any planning or drafting workflow to
    incorporate learned patterns and user preferences.

    Returns:
        Dict with preferences (str) and corrections (str) content.
        Either may be empty if the files don't exist yet.
    """
    vault = settings.vault

    preferences = ""
    if vault.preferences_file.exists():
        preferences = vault.preferences_file.read_text()

    corrections = ""
    if vault.corrections_file.exists():
        corrections = vault.corrections_file.read_text()

    return {
        "preferences": preferences,
        "corrections": corrections,
        "preferences_path": str(vault.preferences_file),
        "corrections_path": str(vault.corrections_file),
    }


def record_correction(
    category: str,
    what_you_did: str,
    what_i_wanted: str,
    ticket_key: str | None = None,
) -> dict:
    """Record a correction to improve future outputs.

    Call this when the user indicates your output was wrong or could
    be better. Categories help organize corrections for later review.

    Args:
        category: Type of correction. Use one of:
            'breakdown' - how to decompose a ticket into subtasks
            'estimation' - complexity or effort estimation
            'comment_draft' - tone, detail level, or framing of Jira comments
            'prioritization' - task ordering or dependency analysis
            'general' - anything else
        what_you_did: Brief description of the agent's output that was wrong.
        what_i_wanted: What the user wanted instead (the correction).
        ticket_key: Optional ticket this correction relates to.

    Returns:
        Confirmation with the correction entry.
    """
    vault = settings.vault
    vault.ensure_dirs()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    ticket_ref = f" ({ticket_key})" if ticket_key else ""

    entry = f"""
### [{category}] {timestamp}{ticket_ref}
- **What you did:** {what_you_did}
- **What I wanted:** {what_i_wanted}
"""

    # Append to corrections file
    corrections_file = vault.corrections_file
    if not corrections_file.exists():
        corrections_file.write_text("# Agent Corrections Log\n\n")

    with open(corrections_file, "a") as f:
        f.write(entry)

    return {
        "status": "recorded",
        "category": category,
        "path": str(corrections_file),
    }


FEEDBACK_TOOLS = [
    get_feedback_context,
    record_correction,
]
