from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelCapabilityRequirement:
    required_tags: set[str] = field(default_factory=set)
    preferred_tags: set[str] = field(default_factory=set)
    min_context_tokens: int = 0
    stream_required: bool = False


@dataclass(frozen=True)
class ModelAccessRequest:
    agent_id: str
    role: str
    task_type: str
    messages: list[dict[str, Any]]
    requirement: ModelCapabilityRequirement | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelAccessResponse:
    content: str
    model: str | None = None
    connector_id: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
