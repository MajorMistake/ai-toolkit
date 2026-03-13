"""Local state tools for Obsidian vault operations.

These manage the private knowledge layer -- ticket notes, sprint plans,
brag doc entries, and feedback. All operations are file-based,
working with markdown files in the vault directory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import structlog

from config.settings import settings

logger = structlog.get_logger(__name__)


# --- Sprint management ---


def get_active_sprint_dir() -> dict:
    """Get the path and contents listing of the current active sprint directory.

    Reads the _index.md file to determine which sprint is active,
    then lists the files in that sprint directory.

    Returns:
        Dict with sprint_dir path, list of ticket files, and sprint plan contents.
    """
    vault = settings.vault
    index_file = vault.index_file

    if not index_file.exists():
        return {"error": "No _index.md found. Run sprint setup first."}

    index_content = index_file.read_text()

    # Parse active sprint from index
    active_sprint = None
    for line in index_content.splitlines():
        if line.startswith("active_sprint:"):
            active_sprint = line.split(":", 1)[1].strip()
            break

    if not active_sprint:
        return {"error": "No active sprint set in _index.md"}

    sprint_dir = vault.sprints_dir / active_sprint
    if not sprint_dir.exists():
        return {"error": f"Sprint directory {active_sprint} does not exist"}

    ticket_files = [f.stem for f in sprint_dir.glob("*.md") if not f.name.startswith("_")]
    sprint_plan = ""
    plan_file = sprint_dir / "_sprint-plan.md"
    if plan_file.exists():
        sprint_plan = plan_file.read_text()

    return {
        "sprint_dir": str(sprint_dir),
        "sprint_name": active_sprint,
        "ticket_files": ticket_files,
        "sprint_plan": sprint_plan,
    }


def setup_sprint(sprint_name: str, goals: str = "") -> dict:
    """Create a new sprint directory and update the index.

    Call this at the start of a new sprint. Creates the directory,
    initializes the sprint plan, and sets it as the active sprint.

    Args:
        sprint_name: Sprint identifier, typically the start date like '2026-03-10'.
        goals: Optional sprint goals to include in the plan.

    Returns:
        Confirmation with the created directory path.
    """
    vault = settings.vault
    vault.ensure_dirs()

    sprint_dir = vault.sprints_dir / sprint_name
    sprint_dir.mkdir(parents=True, exist_ok=True)

    # Create sprint plan
    plan_content = f"""# Sprint {sprint_name}

## Goals
{goals or '[To be filled in during sprint planning]'}

## Capacity Notes
[Energy levels, appointments, known interruptions]

## Retrospective
[Fill in at sprint end]
"""
    plan_file = sprint_dir / "_sprint-plan.md"
    if not plan_file.exists():
        plan_file.write_text(plan_content)

    # Update index
    index_content = f"""# PM Agent Index

active_sprint: {sprint_name}
last_updated: {datetime.now(timezone.utc).isoformat()}
"""
    vault.index_file.write_text(index_content)

    logger.info("sprint_setup", sprint_name=sprint_name, sprint_dir=str(sprint_dir))
    return {
        "status": "created",
        "sprint_dir": str(sprint_dir),
        "sprint_name": sprint_name,
    }


# --- Ticket notes ---


def read_ticket_notes(ticket_key: str) -> dict:
    """Read the local notes file for a specific ticket.

    Returns the full markdown content of the ticket's notes file.
    If no notes exist yet, returns an empty indicator.

    Args:
        ticket_key: The Jira ticket key, e.g. 'DATA-3401'.

    Returns:
        Dict with ticket_key, content (markdown string), and file path.
    """
    vault = settings.vault

    if not vault.sprints_dir.exists():
        return {
            "ticket_key": ticket_key,
            "content": None,
            "message": f"No notes file found for {ticket_key}",
        }

    # Search in all sprint directories for this ticket
    for sprint_dir in vault.sprints_dir.iterdir():
        if not sprint_dir.is_dir():
            continue
        ticket_file = vault.resolve_safe(sprint_dir, f"{ticket_key}.md")
        if ticket_file and ticket_file.exists():
            return {
                "ticket_key": ticket_key,
                "content": ticket_file.read_text(),
                "path": str(ticket_file),
                "sprint": sprint_dir.name,
            }

    return {
        "ticket_key": ticket_key,
        "content": None,
        "message": f"No notes file found for {ticket_key}",
    }


def write_ticket_notes(ticket_key: str, content: str, sprint_name: str | None = None) -> dict:
    """Create or update the local notes file for a ticket.

    If sprint_name is not provided, writes to the active sprint directory.

    Args:
        ticket_key: The Jira ticket key.
        content: Full markdown content to write.
        sprint_name: Optional sprint directory name. Defaults to active sprint.

    Returns:
        Confirmation with the file path.
    """
    vault = settings.vault

    if sprint_name:
        sprint_dir = vault.resolve_safe(vault.sprints_dir, sprint_name)
        if not sprint_dir:
            return {"error": f"Invalid sprint name: {sprint_name}"}
    else:
        # Find active sprint from index
        active = get_active_sprint_dir()
        if "error" in active:
            return active
        sprint_dir = Path(active["sprint_dir"])

    sprint_dir.mkdir(parents=True, exist_ok=True)
    ticket_file = vault.resolve_safe(sprint_dir, f"{ticket_key}.md")
    if not ticket_file:
        return {"error": f"Invalid ticket key: {ticket_key}"}
    ticket_file.write_text(content)

    logger.info("ticket_notes_written", ticket_key=ticket_key, sprint=sprint_dir.name)
    return {
        "status": "written",
        "ticket_key": ticket_key,
        "path": str(ticket_file),
        "sprint": sprint_dir.name,
    }


def create_ticket_note_from_jira(ticket_data: dict, sprint_name: str | None = None) -> dict:
    """Create an initial notes file for a ticket from Jira data.

    Generates the standard template populated with Jira metadata.
    Does NOT overwrite existing notes.

    Args:
        ticket_data: Full ticket dict from get_ticket_details.
        sprint_name: Optional sprint directory name.

    Returns:
        Confirmation or skip if file already exists.
    """
    ticket_key = ticket_data.get("key", "UNKNOWN")

    # Check if notes already exist
    existing = read_ticket_notes(ticket_key)
    if existing.get("content") is not None:
        return {
            "status": "skipped",
            "ticket_key": ticket_key,
            "message": "Notes already exist for this ticket",
            "path": existing.get("path"),
        }

    content = f"""# {ticket_key}: {ticket_data.get('summary', 'No summary')}

## Status
- Jira status: {ticket_data.get('status', 'Unknown')}
- My status: [Not started]
- Story points: {ticket_data.get('story_points', 'Unestimated')}
- Priority: {ticket_data.get('priority', 'Unknown')}
- Last synced: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## Jira Description
{ticket_data.get('description', '[No description]')}

## Breakdown
[Agent will suggest breakdown -- edit and refine]

## Technical Notes
[Your rough notes, approaches, learnings go here]

## Draft Comments
[Agent-drafted text for Jira, review before posting]

## Brag Doc Material
[Agent-drafted STAR entry if this ticket is noteworthy]
"""

    return write_ticket_notes(ticket_key, content, sprint_name)


def move_ticket_to_sprint(ticket_key: str, from_sprint: str, to_sprint: str) -> dict:
    """Move a ticket's notes file from one sprint to another.

    Used for carryover tickets. Moves the file rather than symlinking
    to keep things simple and Obsidian-sync-friendly.

    Args:
        ticket_key: The Jira ticket key.
        from_sprint: Source sprint directory name.
        to_sprint: Destination sprint directory name.

    Returns:
        Confirmation with old and new paths.
    """
    vault = settings.vault
    from_dir = vault.resolve_safe(vault.sprints_dir, from_sprint)
    to_dir = vault.resolve_safe(vault.sprints_dir, to_sprint)
    if not from_dir or not to_dir:
        return {"error": "Invalid sprint name"}
    from_file = vault.resolve_safe(from_dir, f"{ticket_key}.md")
    if not from_file:
        return {"error": f"Invalid ticket key: {ticket_key}"}
    to_dir.mkdir(parents=True, exist_ok=True)
    to_file = vault.resolve_safe(to_dir, f"{ticket_key}.md")
    if not to_file:
        return {"error": f"Invalid ticket key: {ticket_key}"}

    if not from_file.exists():
        return {"error": f"No notes file found for {ticket_key} in sprint {from_sprint}"}

    if to_file.exists():
        return {"error": f"Notes for {ticket_key} already exist in sprint {to_sprint}"}

    # Move the file
    to_file.write_text(from_file.read_text())
    from_file.unlink()

    logger.info(
        "ticket_moved", ticket_key=ticket_key,
        from_sprint=from_sprint, to_sprint=to_sprint,
    )
    return {
        "status": "moved",
        "ticket_key": ticket_key,
        "from": str(from_file),
        "to": str(to_file),
    }


# --- Brag doc ---


def list_brag_entries() -> dict:
    """List all brag doc entries.

    Returns:
        Dict with list of entry filenames and their first line (title).
    """
    vault = settings.vault
    if not vault.brag_doc_dir.exists():
        return {"entries": [], "count": 0}

    entries = []
    for f in sorted(vault.brag_doc_dir.glob("*.md")):
        first_line = ""
        with open(f) as fh:
            first_line = fh.readline().strip().lstrip("# ")
        entries.append({"filename": f.name, "title": first_line})

    return {"entries": entries, "count": len(entries)}


def read_brag_entry(filename: str) -> dict:
    """Read a specific brag doc entry.

    Args:
        filename: The filename in the brag-doc directory.

    Returns:
        Dict with filename and full markdown content.
    """
    vault = settings.vault
    filepath = vault.resolve_safe(vault.brag_doc_dir, filename)
    if not filepath:
        return {"error": "Invalid filename"}
    if not filepath.exists():
        return {"error": f"Brag entry {filename} not found"}
    return {"filename": filename, "content": filepath.read_text()}


def write_brag_entry(ticket_key: str, content: str, date: str | None = None) -> dict:
    """Create a new brag doc entry.

    Entries are named with date prefix and ticket key for natural sorting.

    Args:
        ticket_key: The Jira ticket key this entry relates to.
        content: Full STAR-format markdown content.
        date: Optional date string (YYYY-MM-DD). Defaults to today.

    Returns:
        Confirmation with the file path.
    """
    vault = settings.vault
    vault.ensure_dirs()

    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    filename = f"{date}_{ticket_key}.md"
    filepath = vault.resolve_safe(vault.brag_doc_dir, filename)
    if not filepath:
        return {"error": f"Invalid ticket key: {ticket_key}"}
    filepath.write_text(content)

    logger.info("brag_entry_created", ticket_key=ticket_key, filename=filename)
    return {
        "status": "created",
        "filename": filename,
        "path": str(filepath),
    }


# All local state tools to register with the ADK agent
LOCAL_STATE_TOOLS = [
    get_active_sprint_dir,
    setup_sprint,
    read_ticket_notes,
    write_ticket_notes,
    create_ticket_note_from_jira,
    move_ticket_to_sprint,
    list_brag_entries,
    read_brag_entry,
    write_brag_entry,
]
