# Agent Preferences

## Work Context
- Stack: Python, SQL, BigQuery, Cloud Spanner, Looker, Chronicle SIEM, FastAPI
- CI/CD: GitHub Actions, ArgoCD (recently migrated from Jenkins)
- Current focus areas: data pipelines, dashboards, analytics infrastructure, agent development

## Task Breakdown Preferences
- I think in terms of "what can I ship independently" -- subtasks should be mergeable units, not just TODO items
- For migration tickets (e.g. BigQuery to Spanner), always call out: schema changes, query rewrites, connection/auth changes, testing, rollback plan as separate concerns
- For investigation tickets, the first subtask is always "define what 'done' looks like" -- investigations without exit criteria expand forever
- Pipeline bugs: always include a subtask for "add test/monitoring to catch this class of bug in the future"

## Communication Preferences
- Never use em-dashes in any written output (they read as AI-generated)
- Be concise. I'd rather add detail than remove fluff
- Technical precision matters more than polish
- When drafting comments for leadership visibility (Director, VP-level), lead with impact/outcome, then technical detail

## Estimation Patterns
- I tend to underestimate coordination overhead (meetings, waiting on reviews, context-switching)
- Spanner migration work has historically been 1.5x my initial estimate
- Documentation tasks take longer than I expect -- budget accordingly
- Investigation tickets are the hardest to estimate; default to timeboxing

## Energy Management
- I work best on complex reasoning tasks in the morning
- Afternoons are better for routine tasks, documentation, and communication
- Context-switching is expensive for me -- try to batch related work
- If I have a blocker, suggest switching to an unrelated task rather than grinding on it
