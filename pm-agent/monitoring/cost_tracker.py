"""Cost tracking and observability for all LLM calls.

Logs every LLM call via ADK's after_model_callback with real usage metadata
from the model response. Writes to an append-only JSONL file for analysis.

Usage:
    from config.settings import settings
    tracker = CostTracker(settings.monitoring)

    # Use as ADK after_model_callback (wired automatically in agent.py):
    root_agent = Agent(
        ...,
        after_model_callback=tracker.after_model_callback,
    )

    # Or log manually for testing:
    tracker.log_call(
        model="gemini-2.5-flash",
        input_tokens=150,
        output_tokens=300,
        latency_ms=1200,
        workflow="manual",
    )
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from config.settings import MonitoringConfig, VERTEX_LABELS

logger = structlog.get_logger(__name__)

# Pricing per 1M tokens (Vertex AI, USD).
#
# Estimates for personal cost tracking, not billing-accurate.
# Actual billing comes from GCP. ADK exposes thoughts_token_count
# separately from candidates_token_count, so we price them at their
# respective tiers.
#
# Verify periodically against:
# https://cloud.google.com/vertex-ai/generative-ai/pricing
MODEL_PRICING = {
    # Gemini 2.5 Flash
    "gemini-2.5-flash": {
        "input": 0.15,
        "output": 0.60,
        "thinking": 3.50,
        "cached_input": 0.0375,
    },

    # Gemini 2.5 Pro (<=200K context)
    "gemini-2.5-pro": {
        "input": 1.25,
        "output": 10.00,
        "thinking": 10.00,
        "cached_input": 0.3125,
    },

    # Gemini 3 Flash -- potential future upgrade
    "gemini-3-flash": {
        "input": 0.50,
        "output": 3.00,
        "thinking": 3.00,
        "cached_input": 0.125,
    },

    # Gemini 3.1 Pro -- potential future upgrade
    "gemini-3.1-pro": {
        "input": 2.00,
        "output": 12.00,
        "thinking": 12.00,
        "cached_input": 0.50,
    },

    # Fallback for unknown models
    "default": {
        "input": 0.50,
        "output": 2.00,
        "thinking": 2.00,
        "cached_input": 0.125,
    },
}


class CallRecord(BaseModel):
    """Single LLM call log entry."""

    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int = 0
    cached_input_tokens: int = 0
    total_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    workflow: str
    ticket: str | None = None
    tools_called: list[str] = Field(default_factory=list)
    billing_labels: dict[str, str] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.model_dump_json()


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    thinking_tokens: int = 0,
    cached_input_tokens: int = 0,
) -> float:
    """Estimate USD cost based on Vertex AI pricing tiers.

    Separates thinking tokens (expensive) from regular output tokens.
    Cached input tokens are priced at ~25% of regular input.
    """
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    # Uncached input = total input - cached portion
    uncached_input = max(0, input_tokens - cached_input_tokens)
    input_cost = (uncached_input / 1_000_000) * pricing["input"]
    cached_cost = (cached_input_tokens / 1_000_000) * pricing["cached_input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    thinking_cost = (thinking_tokens / 1_000_000) * pricing["thinking"]
    return round(input_cost + cached_cost + output_cost + thinking_cost, 6)


class CostTracker:
    """Append-only cost and observability logger.

    Integrates with ADK via after_model_callback to automatically log every
    LLM call with real usage metadata from the model response.
    """

    def __init__(self, config: MonitoringConfig) -> None:
        self.config = config
        self.config.ensure_dirs()
        self._log_path = config.cost_log_path
        self._call_start: float | None = None

    def log_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        workflow: str,
        thinking_tokens: int = 0,
        cached_input_tokens: int = 0,
        ticket: str | None = None,
        tools_called: list[str] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CallRecord:
        """Log a single LLM call to the JSONL file."""
        record = CallRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            cached_input_tokens=cached_input_tokens,
            total_tokens=input_tokens + output_tokens + thinking_tokens,
            latency_ms=round(latency_ms, 2),
            estimated_cost_usd=estimate_cost(
                model, input_tokens, output_tokens, thinking_tokens, cached_input_tokens
            ),
            workflow=workflow,
            ticket=ticket,
            tools_called=tools_called or [],
            billing_labels={
                **VERTEX_LABELS,
                "agent": self.config.agent_label,
                "workflow": workflow,
                **({"ticket": ticket} if ticket else {}),
            },
            error=error,
            metadata=metadata or {},
        )

        with open(self._log_path, "a") as f:
            f.write(record.to_json() + "\n")

        logger.info(
            "llm_call_logged",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            total_tokens=record.total_tokens,
            latency_ms=record.latency_ms,
            estimated_cost_usd=record.estimated_cost_usd,
            workflow=workflow,
            ticket=ticket,
        )

        return record

    async def after_model_callback(
        self, *, callback_context: Any, llm_response: Any
    ) -> None:
        """ADK after_model_callback -- logs each LLM call with real usage data.

        Wired into the Agent constructor so it fires automatically on every
        model invocation. Extracts token counts from the LlmResponse's
        usage_metadata, including thinking token breakdown.
        """
        elapsed_ms = 0.0
        if self._call_start is not None:
            elapsed_ms = (time.monotonic() - self._call_start) * 1000
            self._call_start = None

        usage = getattr(llm_response, "usage_metadata", None)
        if usage is None:
            return None

        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0
        cached_tokens = getattr(usage, "cached_content_token_count", 0) or 0

        model_name = getattr(llm_response, "model", None) or "unknown"
        # ADK may return full resource paths like "models/gemini-2.5-flash"
        if "/" in model_name:
            model_name = model_name.rsplit("/", 1)[-1]

        try:
            self.log_call(
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                thinking_tokens=thinking_tokens,
                cached_input_tokens=cached_tokens,
                latency_ms=elapsed_ms,
                workflow="agent",
                metadata={
                    "total_token_count": getattr(usage, "total_token_count", None),
                },
            )
        except Exception:
            logger.exception("llm_call_log_failed")

        return None

    async def before_model_callback(
        self, *, callback_context: Any, llm_request: Any
    ) -> None:
        """Records call start time for latency measurement."""
        self._call_start = time.monotonic()
        return None

    def get_summary(self, days: int = 30) -> dict[str, Any]:
        """Read the log and compute summary statistics."""
        if not self._log_path.exists():
            return {"total_calls": 0, "total_cost_usd": 0.0, "by_workflow": {}, "by_model": {}}

        records = []

        with open(self._log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        by_workflow: dict[str, dict[str, float]] = {}
        by_model: dict[str, dict[str, float]] = {}
        total_cost = 0.0
        total_tokens = 0

        for r in records:
            cost = r.get("estimated_cost_usd", 0.0)
            tokens = r.get("total_tokens", 0)
            total_cost += cost
            total_tokens += tokens

            wf = r.get("workflow", "unknown")
            if wf not in by_workflow:
                by_workflow[wf] = {"calls": 0, "cost_usd": 0.0, "tokens": 0}
            by_workflow[wf]["calls"] += 1
            by_workflow[wf]["cost_usd"] += cost
            by_workflow[wf]["tokens"] += tokens

            model = r.get("model", "unknown")
            if model not in by_model:
                by_model[model] = {"calls": 0, "cost_usd": 0.0, "tokens": 0}
            by_model[model]["calls"] += 1
            by_model[model]["cost_usd"] += cost
            by_model[model]["tokens"] += tokens

        return {
            "total_calls": len(records),
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "by_workflow": by_workflow,
            "by_model": by_model,
        }
