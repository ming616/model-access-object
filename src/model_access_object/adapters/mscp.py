from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from contextlib import AsyncExitStack, asynccontextmanager
from math import isfinite
from typing import TYPE_CHECKING, Any

from ..errors import (
    ModelAccessBusyError,
    ModelAccessError,
    ModelAccessResponseError,
    ModelAccessTimeoutError,
    ModelAccessUnavailableError,
)
from ..types import ModelAccessResponse, ModelCapabilityRequirement

if TYPE_CHECKING:
    from model_service_connector_pool import ModelServiceConnectorPool


class MSCPAdapter:
    """MAO-owned adaptation of MSCP leases to model access operations."""

    def __init__(
        self,
        pool: ModelServiceConnectorPool,
        *,
        acquire_timeout: float | None = 0,
        invocation_timeout: float | None = None,
    ) -> None:
        if invocation_timeout is not None and (
            invocation_timeout <= 0 or not isfinite(invocation_timeout)
        ):
            raise ValueError("invocation_timeout must be finite and positive, or None.")
        self._pool = pool
        self._acquire_timeout = acquire_timeout
        self._invocation_timeout = invocation_timeout

    @staticmethod
    def _requirement(requirement: ModelCapabilityRequirement) -> Any:
        from model_service_connector_pool import CapabilityRequirement

        return CapabilityRequirement(
            required_tags=set(requirement.required_tags),
            preferred_tags=set(requirement.preferred_tags),
            min_context_tokens=requirement.min_context_tokens,
            stream_required=requirement.stream_required,
        )

    @staticmethod
    def _response(payload: Mapping[str, Any], lease: Any) -> ModelAccessResponse:
        if not isinstance(payload, Mapping):
            raise ModelAccessResponseError("A model response must be a mapping.")
        content = payload.get("content")
        if not isinstance(content, str):
            raise ModelAccessResponseError("A model response must contain string content.")
        usage, metadata = payload.get("usage", {}), payload.get("metadata", {})
        if not isinstance(usage, dict) or not isinstance(metadata, dict):
            raise ModelAccessResponseError("Response usage and metadata must be dictionaries.")
        return ModelAccessResponse(
            content=content,
            model=payload.get("model") or lease.metadata.model,
            connector_id=lease.metadata.connector_id,
            usage=dict(usage),
            metadata=dict(metadata),
        )

    @asynccontextmanager
    async def _lease(
        self, agent_id: str, requirement: ModelCapabilityRequirement
    ) -> AsyncIterator[Any]:
        from model_service_connector_pool import (
            AcquireTimeoutError,
            ConnectorUnavailableError,
            NoMatchingConnectorError,
            PoolBusyError,
            PoolClosedError,
        )

        async with AsyncExitStack() as stack:
            try:
                lease = await stack.enter_async_context(
                    self._pool.acquire(
                        agent_id, self._requirement(requirement), timeout=self._acquire_timeout
                    )
                )
            except (NoMatchingConnectorError, ConnectorUnavailableError, PoolClosedError) as error:
                raise ModelAccessUnavailableError(str(error)) from error
            except PoolBusyError as error:
                raise ModelAccessBusyError(str(error)) from error
            except AcquireTimeoutError as error:
                raise ModelAccessTimeoutError(str(error)) from error
            yield lease

    async def invoke_with_requirement(
        self,
        agent_id: str,
        requirement: ModelCapabilityRequirement,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ModelAccessResponse:
        async with self._lease(agent_id, requirement) as lease:
            payload = await self._operation(lease.invoke(messages, **kwargs))
            return self._response(payload, lease)

    @asynccontextmanager
    async def stream_with_requirement(
        self,
        agent_id: str,
        requirement: ModelCapabilityRequirement,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> AsyncIterator[AsyncIterator[ModelAccessResponse]]:
        async with (
            self._lease(agent_id, requirement) as lease,
            lease.stream(messages, **kwargs) as chunks,
        ):
            yield self._responses(chunks, lease)

    async def _responses(
        self, chunks: AsyncIterator[dict[str, Any]], lease: Any
    ) -> AsyncIterator[ModelAccessResponse]:
        while True:
            try:
                payload = await self._operation(anext(chunks))
            except StopAsyncIteration:
                return
            yield self._response(payload, lease)

    async def _operation(self, operation: Any) -> Any:
        from model_service_connector_pool import ModelServiceError

        try:
            return await asyncio.wait_for(operation, self._invocation_timeout)
        except (asyncio.TimeoutError, TimeoutError) as error:
            raise ModelAccessTimeoutError(str(error) or "Model access timed out.") from error
        except ModelServiceError as error:
            raise ModelAccessError(str(error)) from error
