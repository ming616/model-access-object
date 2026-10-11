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
        if explicit is not None:
            return explicit
        if task_type in self._task_requirements:
            return self._task_requirements[task_type]
        if role in self._role_requirements:
            return self._role_requirements[role]
        return ModelCapabilityRequirement()
