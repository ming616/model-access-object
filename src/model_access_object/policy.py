from __future__ import annotations

from .types import ModelCapabilityRequirement


class InMemoryModelAccessPolicy:
    def __init__(self) -> None:
        self._role_requirements: dict[str, ModelCapabilityRequirement] = {}
        self._task_requirements: dict[str, ModelCapabilityRequirement] = {}

    def set_role_requirement(
        self,
        role: str,
        requirement: ModelCapabilityRequirement,
    ) -> None:
        self._role_requirements[role] = requirement

    def set_task_requirement(
        self,
        task_type: str,
        requirement: ModelCapabilityRequirement,
    ) -> None:
        self._task_requirements[task_type] = requirement

    def resolve(
        self,
        role: str,
        task_type: str,
        explicit: ModelCapabilityRequirement | None = None,
    ) -> ModelCapabilityRequirement:
        requirements = [
            item
            for item in (
                self._role_requirements.get(role),
                self._task_requirements.get(task_type),
                explicit,
            )
            if item is not None
        ]
        return ModelCapabilityRequirement(
            required_tags=set().union(*(item.required_tags for item in requirements)),
            preferred_tags=set().union(*(item.preferred_tags for item in requirements)),
            min_context_tokens=max((item.min_context_tokens for item in requirements), default=0),
            stream_required=any(item.stream_required for item in requirements),
        )
