"""Central configuration for the PM agent.

Uses Pydantic BaseSettings for environment variable loading and validation.
Loads .env file automatically via pydantic-settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to the project root (two levels up from config/)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class GCPConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GOOGLE_CLOUD_", env_file=_ENV_FILE, extra="ignore")

    project: str = "cyderes-test"
    location: str = "us-central1"


class JiraConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JIRA_", env_file=_ENV_FILE, populate_by_name=True, extra="ignore"
    )

    base_url: str = ""
    email: str = ""
    api_token: SecretStr = SecretStr("")
    board_id: str = ""
    use_mock: bool = Field(default=True, alias="USE_MOCK_JIRA")
    write_mode: Literal["local_only", "confirm", "live"] = Field(
        default="local_only", alias="JIRA_WRITE_MODE"
    )


class VaultConfig(BaseSettings):
    """Paths within the Obsidian vault for the PM agent."""

    model_config = SettingsConfigDict(
        env_prefix="VAULT_", env_file=_ENV_FILE, populate_by_name=True, extra="ignore"
    )

    root: Path = Field(default=Path("~/obsidian-vault/pm-agent"), alias="VAULT_PATH")

    @field_validator("root", mode="before")
    @classmethod
    def expand_root(cls, v: str | Path) -> Path:
        return Path(v).expanduser()

    @property
    def sprints_dir(self) -> Path:
        return self.root / "sprints"

    @property
    def brag_doc_dir(self) -> Path:
        return self.root / "brag-doc"

    @property
    def feedback_dir(self) -> Path:
        return self.root / "feedback"

    @property
    def index_file(self) -> Path:
        return self.root / "_index.md"

    @property
    def preferences_file(self) -> Path:
        return self.feedback_dir / "preferences.md"

    @property
    def corrections_file(self) -> Path:
        return self.feedback_dir / "corrections.md"

    def ensure_dirs(self) -> None:
        """Create vault directories if they don't exist."""
        for d in [self.sprints_dir, self.brag_doc_dir, self.feedback_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def resolve_safe(self, base_dir: Path, filename: str) -> Path | None:
        """Resolve a filename within base_dir, returning None if it escapes."""
        resolved = (base_dir / filename).resolve()
        if not str(resolved).startswith(str(base_dir.resolve())):
            return None
        return resolved


class MonitoringConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="", env_file=_ENV_FILE, populate_by_name=True, extra="ignore"
    )

    cost_log_path: Path = Field(
        default=Path("~/.pm-agent/cost_log.jsonl"), alias="COST_LOG_PATH"
    )
    agent_label: str = Field(default="pm-agent", alias="AGENT_LABEL")

    @field_validator("cost_log_path", mode="before")
    @classmethod
    def expand_cost_log(cls, v: str | Path) -> Path:
        return Path(v).expanduser()

    def ensure_dirs(self) -> None:
        self.cost_log_path.parent.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    gcp: GCPConfig = Field(default_factory=GCPConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    vault: VaultConfig = Field(default_factory=VaultConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    def initialize(self) -> None:
        """Ensure all required directories exist."""
        self.vault.ensure_dirs()
        self.monitoring.ensure_dirs()


# Singleton for import convenience
settings = Settings()
settings.initialize()
