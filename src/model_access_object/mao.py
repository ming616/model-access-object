from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import replace
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
    ) -> ModelAccessResponse: ...


class StreamingModelConnectorPoolLike(ModelConnectorPoolLike, Protocol):
    def stream_with_requirement(
        self,
        agent_id: str,
        requirement: ModelCapabilityRequirement,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> AbstractAsyncContextManager[AsyncIterator[ModelAccessResponse]]: ...


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
        *,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ModelAccessResponse:
        request = ModelAccessRequest(
            agent_id=agent_id,
            role=role,
            task_type=task_type,
            messages=messages,
            requirement=requirement,
            metadata=dict(metadata or {}),
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
        response = await self._connector_pool.invoke_with_requirement(
            agent_id=request.agent_id,
            requirement=requirement,
            messages=request.messages,
            **kwargs,
        )
        return self._with_metadata(response, request.metadata)

    @asynccontextmanager
    async def stream(
        self,
        agent_id: str,
        role: str,
        task_type: str,
        messages: list[dict[str, Any]],
        requirement: ModelCapabilityRequirement | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[AsyncIterator[ModelAccessResponse]]:
        resolved = self._policy.resolve(role, task_type, requirement)
        resolved = replace(resolved, stream_required=True)
        stream_method = getattr(self._connector_pool, "stream_with_requirement", None)
        if stream_method is None:
            raise NotImplementedError(
                "The configured model access backend does not support streaming."
            )
        async with stream_method(agent_id, resolved, messages, **kwargs) as chunks:
            yield self._stream_metadata(chunks, metadata or {})

    @staticmethod
    def _with_metadata(
        response: ModelAccessResponse, metadata: dict[str, Any]
    ) -> ModelAccessResponse:
        if not metadata:
            return response
        return replace(response, metadata={**response.metadata, "request_metadata": dict(metadata)})

    async def _stream_metadata(
        self, chunks: AsyncIterator[ModelAccessResponse], metadata: dict[str, Any]
    ) -> AsyncIterator[ModelAccessResponse]:
        async for chunk in chunks:
            yield self._with_metadata(chunk, metadata)
