from __future__ import annotations

from typing import Any, Protocol

from .policy import InMemoryModelAccessPolicy
from .types import ModelAccessRequest, ModelAccessResponse, ModelCapabilityRequirement


class ModelConnectorPoolLike(Protocol):
    async def invoke_with_requirement(
        self,
        agent_id: str,
        requirement: ModelCapabilityRequirement,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ModelAccessResponse:
        ...


class ModelAccessObject:
    def __init__(
        self,
        connector_pool: ModelConnectorPoolLike,
        policy: InMemoryModelAccessPolicy | None = None,
    ) -> None:
        self._connector_pool = connector_pool
        self._policy = policy or InMemoryModelAccessPolicy()

    async def chat(
        self,
        agent_id: str,
        role: str,
        task_type: str,
        messages: list[dict[str, Any]],
        requirement: ModelCapabilityRequirement | None = None,
        **kwargs: Any,
    ) -> ModelAccessResponse:
        request = ModelAccessRequest(
            agent_id=agent_id,
            role=role,
            task_type=task_type,
            messages=messages,
            requirement=requirement,
        )
        return await self.execute(request, **kwargs)

    async def execute(
        self,
        request: ModelAccessRequest,
        **kwargs: Any,
    ) -> ModelAccessResponse:
        requirement = self._policy.resolve(
            role=request.role,
            task_type=request.task_type,
            explicit=request.requirement,
        )
        return await self._connector_pool.invoke_with_requirement(
            agent_id=request.agent_id,
            requirement=requirement,
            messages=request.messages,
            **kwargs,
        )
