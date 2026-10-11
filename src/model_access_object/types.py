from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelCapabilityRequirement:
    required_tags: set[str] = field(default_factory=set)
    preferred_tags: set[str] = field(default_factory=set)
    min_context_tokens: int = 0
    stream_required: bool = False

    def __post_init__(self) -> None:
        if self.min_context_tokens < 0:
            raise ValueError("min_context_tokens must be non-negative.")


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

    def to_dict(self) -> dict[str, Any]:
        """Return a detached value snapshot for caller-owned history/checkpoints."""
        return asdict(self)
