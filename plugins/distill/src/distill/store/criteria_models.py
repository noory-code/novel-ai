"""Validated inputs for project criteria."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import PureWindowsPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> str:
    """Return a stable UTC timestamp for persisted records."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class RecordedBy(BaseModel):
    """Host metadata supplied by the caller that captured a source."""

    model_config = ConfigDict(extra="forbid")

    host: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    via: str = Field(min_length=1)

    @field_validator("host", "session_id", "via")
    @classmethod
    def require_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source metadata must not be blank")
        return value


class Origin(BaseModel):
    """Immutable source evidence for one criterion version or event."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["user_statement", "stage_card", "stage_decision"]
    source_ref: str = Field(min_length=1)
    quote: str = Field(min_length=1, max_length=2000)
    quote_sha256: str | None = None
    source_sha256: str | None = None
    actor: Literal["user", "ai"]
    recorded_by: RecordedBy
    captured_at: str | None = None

    @field_validator("quote", "source_ref")
    @classmethod
    def require_nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("source evidence must not be blank")
        return value

    @model_validator(mode="after")
    def complete_derived_fields(self) -> Origin:
        if self.kind == "user_statement":
            if not re.fullmatch(r"session:[^/\s]+/[^/\s]+/\S+", self.source_ref):
                raise ValueError("source_ref must identify a session message")
            if self.source_sha256 is not None:
                raise ValueError("a session source must not claim a checked source hash")
        elif not self.source_ref.startswith("stage:") or "#" not in self.source_ref:
            raise ValueError("source_ref must identify a Stage section")
        elif not self.source_sha256 or not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise ValueError("a Stage source requires its section hash")
        digest = hashlib.sha256(self.quote.encode("utf-8")).hexdigest()
        if self.quote_sha256 is not None and self.quote_sha256 != digest:
            raise ValueError("quote_sha256 does not match quote")
        self.quote_sha256 = digest
        if self.captured_at is None:
            self.captured_at = utc_now()
        return self


class Condition(BaseModel):
    """One AND condition whose values are alternatives."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["path", "work_kind"]
    any: list[str] = Field(min_length=1)

    @field_validator("any")
    @classmethod
    def validate_values(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("condition values must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_path_values(self) -> Condition:
        if self.kind != "path":
            return self
        for value in self.any:
            parts = value.replace("\\", "/").split("/")
            if value.startswith(("/", "\\")) or PureWindowsPath(value).drive or ".." in parts:
                raise ValueError("paths must be repository-relative")
            if any(character in value for character in "*?["):
                raise ValueError("glob paths are not supported")
        return self


class CriterionFields(BaseModel):
    """Meaningful fields shared by records and versions."""

    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=1, max_length=2000)
    applies_when: list[Condition] = Field(default_factory=list)
    exceptions: list[Condition] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    overrides: list[str] = Field(default_factory=list)
    confirmation: Literal["user_stated", "none"]
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    origin: Origin

    @field_validator("statement")
    @classmethod
    def clean_statement(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("statement must not be empty")
        return cleaned

    @field_validator("notes", "overrides")
    @classmethod
    def validate_short_strings(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("list values must not be empty")
        if any(len(value) > 2000 for value in cleaned):
            raise ValueError("list values must not exceed 2000 characters")
        return cleaned

    @model_validator(mode="after")
    def validate_confirmation(self) -> CriterionFields:
        if self.confirmation == "user_stated" and self.origin.actor != "user":
            raise ValueError("user_stated requires a user source")
        if self.confirmation == "none" and self.origin.actor != "ai":
            raise ValueError("unconfirmed criteria require an AI source")
        if self.overrides and self.origin.actor != "user":
            raise ValueError("overrides require a user source")
        return self


class RecordRequest(CriterionFields):
    """Input for a new project criterion."""

    project: str = Field(min_length=1)

    @field_validator("project")
    @classmethod
    def clean_project(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("project must not be empty")
        return cleaned


class ReviseRequest(BaseModel):
    """A partial update that creates a new immutable version."""

    model_config = ConfigDict(extra="forbid")

    base_version: int = Field(ge=1)
    project: str | None = None
    statement: str | None = Field(default=None, min_length=1, max_length=2000)
    applies_when: list[Condition] | None = None
    exceptions: list[Condition] | None = None
    notes: list[str] | None = None
    overrides: list[str] | None = None
    confirmation: Literal["user_stated", "none"] | None = None
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    origin: Origin
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("project", "statement", "reason")
    @classmethod
    def clean_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("text must not be empty")
        return cleaned

    @field_validator("notes", "overrides")
    @classmethod
    def validate_optional_lists(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        return CriterionFields.validate_short_strings(values)


class RevokeRequest(BaseModel):
    """Input for retiring the current criterion version."""

    model_config = ConfigDict(extra="forbid")

    base_version: int = Field(ge=1)
    origin: Origin
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("reason must not be empty")
        return cleaned
