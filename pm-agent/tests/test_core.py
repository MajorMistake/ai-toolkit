"""Smoke tests for core modules.

Run with: pytest tests/ -v
"""

from __future__ import annotations

import json
import sys

import pytest
from pydantic import ValidationError

from config.settings import Settings, VaultConfig, MonitoringConfig, JiraConfig
from monitoring.cost_tracker import CostTracker, CallRecord, estimate_cost, MODEL_PRICING


# --- Pydantic model validation tests ---


class TestPydanticModels:
    def test_jira_config_defaults(self):
        config = JiraConfig()
        assert config.write_mode == "local_only"
        assert config.use_mock is True

    def test_jira_config_write_mode_validation(self):
        config = JiraConfig(write_mode="confirm")
        assert config.write_mode == "confirm"

    def test_jira_config_invalid_write_mode(self):
        with pytest.raises(ValidationError):
            JiraConfig(write_mode="invalid_mode")

    def test_vault_config_expands_home(self, tmp_path):
        config = VaultConfig(root=tmp_path / "vault")
        assert config.root == tmp_path / "vault"
        assert not str(config.root).startswith("~")

    def test_settings_nested_construction(self, tmp_path):
        s = Settings(
            vault=VaultConfig(root=tmp_path / "vault"),
            monitoring=MonitoringConfig(cost_log_path=tmp_path / "log.jsonl"),
        )
        assert s.vault.root == tmp_path / "vault"
        assert s.monitoring.cost_log_path == tmp_path / "log.jsonl"

    def test_call_record_model(self):
        record = CallRecord(
            timestamp="2026-03-12T00:00:00Z",
            model="gemini-2.5-flash",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300,
            latency_ms=500.0,
            estimated_cost_usd=0.001,
            workflow="test",
        )
        assert record.model == "gemini-2.5-flash"
        assert record.total_tokens == 300

        # Serialization round-trip
        data = json.loads(record.to_json())
        assert data["model"] == "gemini-2.5-flash"
        assert data["total_tokens"] == 300

    def test_call_record_rejects_bad_types(self):
        with pytest.raises(ValidationError):
            CallRecord(
                timestamp="2026-03-12T00:00:00Z",
                model="gemini-2.5-flash",
                input_tokens="not_a_number",
                output_tokens=200,
                total_tokens=300,
                latency_ms=500.0,
                estimated_cost_usd=0.001,
                workflow="test",
            )


# --- Cost tracker tests ---


class TestEstimateCost:
    def test_flash_model(self):
        cost = estimate_cost("gemini-2.5-flash", input_tokens=1000, output_tokens=500)
        assert cost > 0
        assert cost < 0.01  # flash should be cheap

    def test_pro_model_more_expensive(self):
        flash_cost = estimate_cost("gemini-2.5-flash", 1000, 1000)
        pro_cost = estimate_cost("gemini-2.5-pro", 1000, 1000)
        assert pro_cost > flash_cost

    def test_unknown_model_uses_default(self):
        cost = estimate_cost("some-future-model", 1000, 1000)
        assert cost > 0

    def test_zero_tokens(self):
        cost = estimate_cost("gemini-2.5-flash", 0, 0)
        assert cost == 0.0

    def test_thinking_tokens_cost_more(self):
        """Thinking tokens should be priced at a higher tier than regular output."""
        output_only = estimate_cost("gemini-2.5-flash", 0, 0, thinking_tokens=0)
        with_thinking = estimate_cost("gemini-2.5-flash", 0, 0, thinking_tokens=1000)
        assert with_thinking > output_only

    def test_cached_input_cheaper(self):
        """Cached input tokens should cost less than uncached."""
        uncached = estimate_cost("gemini-2.5-flash", input_tokens=1000, output_tokens=0)
        cached = estimate_cost(
            "gemini-2.5-flash", input_tokens=1000, output_tokens=0, cached_input_tokens=1000
        )
        assert cached < uncached

    def test_pricing_has_all_tiers(self):
        """Every model entry should have input, output, thinking, cached_input."""
        for model_name, pricing in MODEL_PRICING.items():
            assert "input" in pricing, f"{model_name} missing input"
            assert "output" in pricing, f"{model_name} missing output"
            assert "thinking" in pricing, f"{model_name} missing thinking"
            assert "cached_input" in pricing, f"{model_name} missing cached_input"

    def test_pricing_includes_expected_models(self):
        assert "gemini-2.5-flash" in MODEL_PRICING
        assert "gemini-2.5-pro" in MODEL_PRICING
        assert "default" in MODEL_PRICING


class TestCostTracker:
    def test_log_call_creates_file(self, tmp_path):
        config = MonitoringConfig(cost_log_path=tmp_path / "test_log.jsonl")
        tracker = CostTracker(config)

        record = tracker.log_call(
            model="gemini-2.5-flash",
            input_tokens=100,
            output_tokens=200,
            latency_ms=500.0,
            workflow="test",
        )

        assert record.model == "gemini-2.5-flash"
        assert record.total_tokens == 300
        assert config.cost_log_path.exists()

        # Verify JSONL format
        with open(config.cost_log_path) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["model"] == "gemini-2.5-flash"
            assert data["billing_labels"]["workflow"] == "test"

    def test_log_multiple_calls(self, tmp_path):
        config = MonitoringConfig(cost_log_path=tmp_path / "test_log.jsonl")
        tracker = CostTracker(config)

        tracker.log_call("gemini-2.5-flash", 100, 200, 500.0, "planning")
        tracker.log_call("gemini-2.5-pro", 500, 1000, 2000.0, "breakdown")

        with open(config.cost_log_path) as f:
            lines = f.readlines()
            assert len(lines) == 2

    def test_get_summary(self, tmp_path):
        config = MonitoringConfig(cost_log_path=tmp_path / "test_log.jsonl")
        tracker = CostTracker(config)

        tracker.log_call("gemini-2.5-flash", 100, 200, 500.0, "planning")
        tracker.log_call("gemini-2.5-flash", 200, 400, 800.0, "planning")
        tracker.log_call("gemini-2.5-pro", 500, 1000, 2000.0, "breakdown")

        summary = tracker.get_summary()
        assert summary["total_calls"] == 3
        assert "planning" in summary["by_workflow"]
        assert summary["by_workflow"]["planning"]["calls"] == 2
        assert "gemini-2.5-pro" in summary["by_model"]

    def test_summary_empty_log(self, tmp_path):
        config = MonitoringConfig(cost_log_path=tmp_path / "empty.jsonl")
        tracker = CostTracker(config)
        summary = tracker.get_summary()
        assert summary["total_calls"] == 0

    @pytest.mark.asyncio
    async def test_after_model_callback(self, tmp_path):
        """Simulate ADK after_model_callback with a mock LlmResponse."""
        config = MonitoringConfig(cost_log_path=tmp_path / "test_log.jsonl")
        tracker = CostTracker(config)

        # Simulate the before callback to start the timer
        await tracker.before_model_callback(callback_context=None, llm_request=None)

        # Build a mock LlmResponse with usage_metadata
        class MockUsage:
            prompt_token_count = 500
            candidates_token_count = 200
            thoughts_token_count = 150
            cached_content_token_count = 100
            total_token_count = 850

        class MockResponse:
            model = "models/gemini-2.5-flash"
            usage_metadata = MockUsage()

        await tracker.after_model_callback(
            callback_context=None, llm_response=MockResponse()
        )

        summary = tracker.get_summary()
        assert summary["total_calls"] == 1

        # Verify the logged record has correct token breakdown
        with open(config.cost_log_path) as f:
            record = json.loads(f.readline())
        assert record["model"] == "gemini-2.5-flash"  # stripped "models/" prefix
        assert record["input_tokens"] == 500
        assert record["output_tokens"] == 200
        assert record["thinking_tokens"] == 150
        assert record["cached_input_tokens"] == 100
        assert record["latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_callback_handles_missing_usage(self, tmp_path):
        """Callback should silently skip if usage_metadata is None."""
        config = MonitoringConfig(cost_log_path=tmp_path / "test_log.jsonl")
        tracker = CostTracker(config)

        class MockResponse:
            model = "gemini-2.5-flash"
            usage_metadata = None

        await tracker.after_model_callback(
            callback_context=None, llm_response=MockResponse()
        )

        summary = tracker.get_summary()
        assert summary["total_calls"] == 0


# --- Jira tools tests ---


class TestJiraTools:
    def test_get_sprint_tickets_returns_list(self):
        from tools.jira_tools import get_sprint_tickets

        tickets = get_sprint_tickets()
        assert isinstance(tickets, list)
        assert len(tickets) > 0
        assert all("key" in t for t in tickets)

    def test_get_ticket_details_found(self):
        from tools.jira_tools import get_ticket_details

        result = get_ticket_details("DATA-3401")
        assert result["key"] == "DATA-3401"
        assert "description" in result
        assert "comments" in result

    def test_get_ticket_details_not_found(self):
        from tools.jira_tools import get_ticket_details

        result = get_ticket_details("FAKE-9999")
        assert "error" in result

    def test_post_comment_mock(self):
        from tools.jira_tools import post_comment

        result = post_comment("DATA-3420", "Test comment")
        assert result["status"] == "posted"
        assert result["mock"] is True

    def test_create_subtask_mock(self):
        from tools.jira_tools import create_subtask

        result = create_subtask("DATA-3420", "Write unit tests for CSV export")
        assert result["status"] == "created"
        assert "subtask" in result


# --- Local state tools tests ---


class TestLocalStateTools:
    @pytest.fixture(autouse=True)
    def setup_vault(self, tmp_path, monkeypatch):
        """Point vault to a temp directory for each test."""
        vault_config = VaultConfig(root=tmp_path / "vault" / "pm-agent")
        test_settings = Settings(vault=vault_config)
        test_settings.initialize()

        # Monkeypatch the settings singleton
        settings_module = sys.modules["config.settings"]
        monkeypatch.setattr(settings_module, "settings", test_settings)
        import tools.local_state_tools
        monkeypatch.setattr(tools.local_state_tools, "settings", test_settings)
        import tools.feedback_tools
        monkeypatch.setattr(tools.feedback_tools, "settings", test_settings)

        self.vault_root = vault_config.root

    def test_setup_sprint(self):
        from tools.local_state_tools import setup_sprint, get_active_sprint_dir

        result = setup_sprint("2026-03-10", goals="Ship Spanner migration")
        assert result["status"] == "created"
        assert (self.vault_root / "sprints" / "2026-03-10" / "_sprint-plan.md").exists()

        active = get_active_sprint_dir()
        assert active["sprint_name"] == "2026-03-10"

    def test_write_and_read_ticket_notes(self):
        from tools.local_state_tools import (
            setup_sprint,
            write_ticket_notes,
            read_ticket_notes,
        )

        setup_sprint("2026-03-10")
        write_ticket_notes("DATA-3401", "# Test notes\nSome content here")
        result = read_ticket_notes("DATA-3401")
        assert result["content"] is not None
        assert "Test notes" in result["content"]

    def test_create_ticket_note_from_jira(self):
        from tools.local_state_tools import (
            setup_sprint,
            create_ticket_note_from_jira,
            read_ticket_notes,
        )
        from tools.jira_tools import get_ticket_details

        setup_sprint("2026-03-10")
        ticket = get_ticket_details("DATA-3401")
        result = create_ticket_note_from_jira(ticket)
        assert result["status"] == "written"

        notes = read_ticket_notes("DATA-3401")
        assert "TTR compliance" in notes["content"]

    def test_create_ticket_note_skips_existing(self):
        from tools.local_state_tools import (
            setup_sprint,
            create_ticket_note_from_jira,
        )
        from tools.jira_tools import get_ticket_details

        setup_sprint("2026-03-10")
        ticket = get_ticket_details("DATA-3401")
        create_ticket_note_from_jira(ticket)
        result = create_ticket_note_from_jira(ticket)
        assert result["status"] == "skipped"

    def test_move_ticket_to_sprint(self):
        from tools.local_state_tools import (
            setup_sprint,
            write_ticket_notes,
            move_ticket_to_sprint,
            read_ticket_notes,
        )

        setup_sprint("2026-03-10")
        write_ticket_notes("DATA-3401", "# Notes", sprint_name="2026-03-10")

        setup_sprint("2026-03-24")
        result = move_ticket_to_sprint("DATA-3401", "2026-03-10", "2026-03-24")
        assert result["status"] == "moved"

        notes = read_ticket_notes("DATA-3401")
        assert notes["sprint"] == "2026-03-24"

    def test_brag_doc_workflow(self):
        from tools.local_state_tools import write_brag_entry, list_brag_entries, read_brag_entry

        write_brag_entry("DATA-3401", "# STAR Entry\n\n## Situation\nTTR needed migration...")
        entries = list_brag_entries()
        assert entries["count"] == 1

        content = read_brag_entry(entries["entries"][0]["filename"])
        assert "STAR Entry" in content["content"]


# --- Feedback tools tests ---


class TestFeedbackTools:
    @pytest.fixture(autouse=True)
    def setup_vault(self, tmp_path, monkeypatch):
        vault_config = VaultConfig(root=tmp_path / "vault" / "pm-agent")
        test_settings = Settings(vault=vault_config)
        test_settings.initialize()

        settings_module = sys.modules["config.settings"]
        monkeypatch.setattr(settings_module, "settings", test_settings)
        import tools.feedback_tools
        monkeypatch.setattr(tools.feedback_tools, "settings", test_settings)

    def test_record_and_retrieve_correction(self):
        from tools.feedback_tools import record_correction, get_feedback_context

        record_correction(
            category="breakdown",
            what_you_did="Suggested 3 subtasks for a migration ticket",
            what_i_wanted="Always include a rollback plan as a separate subtask",
            ticket_key="DATA-3401",
        )

        ctx = get_feedback_context()
        assert "rollback plan" in ctx["corrections"]
        assert "breakdown" in ctx["corrections"]

    def test_empty_feedback_context(self):
        from tools.feedback_tools import get_feedback_context

        ctx = get_feedback_context()
        assert ctx["preferences"] == ""
        assert ctx["corrections"] == ""
