"""Planner agent definition using Google ADK.

This is the single agent for the PM system. It has access to:
- Jira tools (read/write, currently mocked)
- Local state tools (Obsidian vault operations)
- Feedback tools (learning from corrections)

The agent uses Gemini Flash by default for cost efficiency.
Switch to gemini-2.5-pro for complex planning sessions if needed.
"""

from __future__ import annotations

from pathlib import Path

from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig

from config.settings import settings
from monitoring.cost_tracker import CostTracker
from tools import ALL_TOOLS

# Load system prompt from markdown file
_PROMPT_DIR = Path(__file__).parent / "prompts"
_SYSTEM_PROMPT = (_PROMPT_DIR / "system_prompt.md").read_text()

# Cost tracker -- logs every LLM call to JSONL with real usage metadata
_tracker = CostTracker(settings.monitoring)

# Labels sent to Vertex AI on every GenerateContent request for GCP cost attribution.
_VERTEX_LABELS = {
    "cy_dept": "engineering",
    "cy_dept_group": "analytics",
    "cy_project": "pm_agent",
    "cy_env_type": "testing",
    "agent": settings.monitoring.agent_label,
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
    generate_content_config=GenerateContentConfig(labels=_VERTEX_LABELS),
    before_model_callback=_tracker.before_model_callback,
    after_model_callback=_tracker.after_model_callback,
)
