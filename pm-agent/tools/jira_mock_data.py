"""Mock Jira data for development and testing.

This module provides realistic ticket data that mirrors actual sprint work
patterns. Tickets cover the range of work types Jackson encounters:
data pipelines, dashboards, BigQuery/Spanner work, automation, and
investigation tasks.

When switching to real Jira, this module gets replaced entirely --
the tool interface stays the same.
"""

from __future__ import annotations

from datetime import datetime, timedelta

# Current mock sprint dates
SPRINT_START = datetime(2026, 3, 10)
SPRINT_END = SPRINT_START + timedelta(days=13)

MOCK_SPRINT = {
    "id": 142,
    "name": "Sprint 2026-03-10",
    "state": "active",
    "start_date": SPRINT_START.isoformat(),
    "end_date": SPRINT_END.isoformat(),
    "board_id": "board-47",
}

MOCK_TICKETS: dict[str, dict] = {
    "DATA-3401": {
        "key": "DATA-3401",
        "summary": "Migrate TTR compliance dashboard from BigQuery to Spanner backend",
        "description": (
            "The TTR compliance dashboard currently reads from BigQuery views. "
            "As part of the Spanner migration effort, update the data source to read "
            "from the new Spanner tables. Ensure no regression in dashboard metrics. "
            "Coordinate with Looker team on connection changes."
        ),
        "type": "Story",
        "status": "To Do",
        "priority": "High",
        "assignee": "jackson",
        "reporter": "victor.otazu",
        "sprint": "Sprint 2026-03-10",
        "story_points": 8,
        "labels": ["migration", "spanner", "looker"],
        "created": "2026-03-08T10:00:00Z",
        "updated": "2026-03-08T10:00:00Z",
        "subtasks": [],
        "links": [
            {"type": "is blocked by", "key": "DATA-3389", "summary": "Spanner table schema finalization"},
        ],
        "comments": [
            {
                "author": "victor.otazu",
                "body": "Prioritizing this -- leadership wants TTR on Spanner by end of Q1.",
                "created": "2026-03-08T14:00:00Z",
            }
        ],
    },
    "DATA-3415": {
        "key": "DATA-3415",
        "summary": "Investigate VertexAI spend spike in February billing",
        "description": (
            "February VertexAI costs were 3x January. Need to identify which "
            "projects/models are driving the increase. Check BigQuery labels, "
            "VertexAI job history, and cross-reference with team usage. "
            "Produce a brief for Nancy."
        ),
        "type": "Task",
        "status": "In Progress",
        "priority": "High",
        "assignee": "jackson",
        "reporter": "nancy.director",
        "sprint": "Sprint 2026-03-10",
        "story_points": 5,
        "labels": ["finops", "vertex-ai", "investigation"],
        "created": "2026-03-06T09:00:00Z",
        "updated": "2026-03-10T11:00:00Z",
        "subtasks": [],
        "links": [],
        "comments": [
            {
                "author": "nancy.director",
                "body": "Need this by Thursday if possible. Leadership meeting Friday.",
                "created": "2026-03-06T09:30:00Z",
            },
            {
                "author": "jackson",
                "body": "Started pulling billing export data. Will have initial findings tomorrow.",
                "created": "2026-03-10T11:00:00Z",
            },
        ],
    },
    "DATA-3420": {
        "key": "DATA-3420",
        "summary": "Add CSV export endpoint to FastAPI analytics service",
        "description": (
            "Users have requested the ability to export dashboard data as CSV. "
            "Add a /export/csv endpoint to the FastAPI service that accepts the "
            "same filter parameters as the existing /data endpoint. Include "
            "proper content-disposition headers."
        ),
        "type": "Story",
        "status": "To Do",
        "priority": "Medium",
        "assignee": "jackson",
        "reporter": "victor.otazu",
        "sprint": "Sprint 2026-03-10",
        "story_points": 3,
        "labels": ["fastapi", "feature"],
        "created": "2026-03-09T15:00:00Z",
        "updated": "2026-03-09T15:00:00Z",
        "subtasks": [],
        "links": [],
        "comments": [],
    },
    "DATA-3422": {
        "key": "DATA-3422",
        "summary": "KnowBe4 automation: handle new campaign type in ingestion pipeline",
        "description": (
            "KnowBe4 introduced a new campaign type 'targeted_phishing_v2' that "
            "our ingestion pipeline doesn't recognize. Pipeline currently drops "
            "these records silently. Need to update the parser and add the new "
            "fields to the BigQuery schema."
        ),
        "type": "Bug",
        "status": "To Do",
        "priority": "Medium",
        "assignee": "jackson",
        "reporter": "jackson",
        "sprint": "Sprint 2026-03-10",
        "story_points": 3,
        "labels": ["knowbe4", "pipeline", "bug"],
        "created": "2026-03-10T08:00:00Z",
        "updated": "2026-03-10T08:00:00Z",
        "subtasks": [],
        "links": [],
        "comments": [],
    },
    "DATA-3430": {
        "key": "DATA-3430",
        "summary": "Document CI/CD migration patterns for team runbook",
        "description": (
            "After the jira-all-projects-collector Jenkins-to-ArgoCD migration, "
            "document the patterns and gotchas for the team. This should cover "
            "GitHub Actions workflow structure, ArgoCD app-of-apps pattern, "
            "and common pitfalls."
        ),
        "type": "Task",
        "status": "To Do",
        "priority": "Low",
        "assignee": "jackson",
        "reporter": "jackson",
        "sprint": "Sprint 2026-03-10",
        "story_points": 2,
        "labels": ["documentation", "ci-cd"],
        "created": "2026-03-10T09:00:00Z",
        "updated": "2026-03-10T09:00:00Z",
        "subtasks": [],
        "links": [],
        "comments": [],
    },
}

# Simulated board configuration
MOCK_BOARD = {
    "id": "board-47",
    "name": "Data Engineering",
    "project_key": "DATA",
    "columns": [
        {"name": "To Do", "statuses": ["To Do"]},
        {"name": "In Progress", "statuses": ["In Progress"]},
        {"name": "In Review", "statuses": ["In Review"]},
        {"name": "Done", "statuses": ["Done"]},
    ],
}

# Available status transitions (simplified)
MOCK_TRANSITIONS = {
    "To Do": [
        {"id": "21", "name": "Start Progress", "to": "In Progress"},
    ],
    "In Progress": [
        {"id": "31", "name": "Submit for Review", "to": "In Review"},
        {"id": "11", "name": "Back to To Do", "to": "To Do"},
    ],
    "In Review": [
        {"id": "41", "name": "Done", "to": "Done"},
        {"id": "21", "name": "Reopen", "to": "In Progress"},
    ],
}
