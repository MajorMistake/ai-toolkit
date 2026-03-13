"""Jira tools for the PM agent.

These are registered as ADK tools on the Planner agent. Each function
has a clear docstring that the LLM uses to decide when/how to call it.

The mock/live switch is handled at the data layer -- these functions
call the appropriate backend based on config.USE_MOCK_JIRA.

When writing real Jira implementations, the function signatures and
return types stay identical. Only the internal implementation changes.
"""

from __future__ import annotations

from tools.jira_mock_data import (
    MOCK_TICKETS,
    MOCK_SPRINT,
    MOCK_TRANSITIONS,
)


def get_current_sprint() -> dict:
    """Get the current active sprint info including name, dates, and state.

    Returns:
        Dict with sprint id, name, state, start_date, end_date, and board_id.
    """
    # TODO: Real implementation uses Jira REST API:
    # GET /rest/agile/1.0/board/{boardId}/sprint?state=active
    return MOCK_SPRINT


def get_sprint_tickets(sprint_id: int | None = None) -> list[dict]:
    """Get all tickets assigned to me in the current sprint.

    Args:
        sprint_id: Optional sprint ID. If not provided, uses current active sprint.

    Returns:
        List of ticket dicts with key, summary, status, priority, story_points,
        and labels. Does NOT include full descriptions or comments -- use
        get_ticket_details for those.
    """
    # TODO: Real implementation uses:
    # GET /rest/agile/1.0/sprint/{sprintId}/issue?jql=assignee=currentUser()
    return [
        {
            "key": t["key"],
            "summary": t["summary"],
            "type": t["type"],
            "status": t["status"],
            "priority": t["priority"],
            "story_points": t["story_points"],
            "labels": t["labels"],
        }
        for t in MOCK_TICKETS.values()
    ]


def get_ticket_details(ticket_key: str) -> dict:
    """Get full details for a specific Jira ticket.

    Includes description, comments, subtasks, links, and all metadata.
    Use this when you need the full context to break down a ticket or
    draft a comment.

    Args:
        ticket_key: The Jira ticket key, e.g. 'DATA-3401'.

    Returns:
        Full ticket dict, or error dict if ticket not found.
    """
    # TODO: Real implementation uses:
    # GET /rest/api/3/issue/{issueIdOrKey}?expand=changelog
    ticket = MOCK_TICKETS.get(ticket_key)
    if not ticket:
        return {"error": f"Ticket {ticket_key} not found"}
    return ticket


def get_ticket_transitions(ticket_key: str) -> list[dict]:
    """Get available status transitions for a ticket.

    Use this to determine what status changes are possible before
    suggesting or making a transition.

    Args:
        ticket_key: The Jira ticket key.

    Returns:
        List of transition dicts with id, name, and target status.
    """
    # TODO: Real implementation uses:
    # GET /rest/api/3/issue/{issueIdOrKey}/transitions
    ticket = MOCK_TICKETS.get(ticket_key)
    if not ticket:
        return [{"error": f"Ticket {ticket_key} not found"}]
    current_status = ticket["status"]
    return MOCK_TRANSITIONS.get(current_status, [])


def post_comment(ticket_key: str, comment_body: str) -> dict:
    """Post a comment to a Jira ticket.

    IMPORTANT: This is a WRITE operation. The agent should always present
    the drafted comment to the user for review before calling this.

    Args:
        ticket_key: The Jira ticket key.
        comment_body: The comment text to post (supports Jira markdown).

    Returns:
        Confirmation dict with the posted comment details.
    """
    # TODO: Real implementation uses:
    # POST /rest/api/3/issue/{issueIdOrKey}/comment
    ticket = MOCK_TICKETS.get(ticket_key)
    if not ticket:
        return {"error": f"Ticket {ticket_key} not found"}

    # In mock mode, append to the ticket's comments in memory
    new_comment = {
        "author": "jackson",
        "body": comment_body,
        "created": "2026-03-11T12:00:00Z",
    }
    ticket["comments"].append(new_comment)

    return {
        "status": "posted",
        "ticket": ticket_key,
        "comment": new_comment,
        "mock": True,
    }


def update_ticket_status(ticket_key: str, transition_id: str) -> dict:
    """Transition a ticket to a new status.

    IMPORTANT: This is a WRITE operation. The agent should always confirm
    the transition with the user before calling this.

    Args:
        ticket_key: The Jira ticket key.
        transition_id: The transition ID (from get_ticket_transitions).

    Returns:
        Confirmation dict with old and new status.
    """
    # TODO: Real implementation uses:
    # POST /rest/api/3/issue/{issueIdOrKey}/transitions
    ticket = MOCK_TICKETS.get(ticket_key)
    if not ticket:
        return {"error": f"Ticket {ticket_key} not found"}

    current_status = ticket["status"]
    transitions = MOCK_TRANSITIONS.get(current_status, [])
    transition = next((t for t in transitions if t["id"] == transition_id), None)

    if not transition:
        return {"error": f"Invalid transition {transition_id} from status {current_status}"}

    old_status = ticket["status"]
    ticket["status"] = transition["to"]

    return {
        "status": "transitioned",
        "ticket": ticket_key,
        "from": old_status,
        "to": transition["to"],
        "mock": True,
    }


def create_subtask(parent_key: str, summary: str, description: str = "") -> dict:
    """Create a subtask under a parent ticket.

    IMPORTANT: This is a WRITE operation. The agent should always present
    the proposed subtask to the user for approval before calling this.

    Args:
        parent_key: The parent Jira ticket key.
        summary: Short summary of the subtask.
        description: Detailed description (optional).

    Returns:
        Confirmation dict with the new subtask details.
    """
    # TODO: Real implementation uses:
    # POST /rest/api/3/issue (with parent field)
    parent = MOCK_TICKETS.get(parent_key)
    if not parent:
        return {"error": f"Parent ticket {parent_key} not found"}

    # Generate a mock subtask key
    subtask_num = 3500 + len(MOCK_TICKETS)
    subtask_key = f"DATA-{subtask_num}"

    subtask = {
        "key": subtask_key,
        "summary": summary,
        "description": description,
        "type": "Sub-task",
        "status": "To Do",
        "priority": parent["priority"],
        "assignee": "jackson",
        "reporter": "jackson",
        "sprint": parent["sprint"],
        "story_points": None,
        "labels": parent["labels"],
        "parent": parent_key,
        "created": "2026-03-11T12:00:00Z",
        "updated": "2026-03-11T12:00:00Z",
        "subtasks": [],
        "links": [],
        "comments": [],
    }

    # Register in mock data
    MOCK_TICKETS[subtask_key] = subtask
    parent["subtasks"].append({"key": subtask_key, "summary": summary, "status": "To Do"})

    return {
        "status": "created",
        "subtask": subtask_key,
        "parent": parent_key,
        "summary": summary,
        "mock": True,
    }


# All tools to register with the ADK agent
JIRA_TOOLS = [
    get_current_sprint,
    get_sprint_tickets,
    get_ticket_details,
    get_ticket_transitions,
    post_comment,
    update_ticket_status,
    create_subtask,
]
