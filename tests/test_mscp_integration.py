import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest

from model_access_object import (
    InMemoryModelAccessPolicy,
    ModelAccessBusyError,
    ModelAccessObject,
    ModelAccessResponseError,
    ModelAccessTimeoutError,
    ModelAccessUnavailableError,
    ModelCapabilityRequirement,
    MSCPAdapter,
)

mscp = pytest.importorskip(
    "model_service_connector_pool",
    reason="Install the paired MSCP source to run integration tests.",
)
CapabilityRequirement = mscp.CapabilityRequirement
InMemoryConnectorRegistry = mscp.InMemoryConnectorRegistry
MockModelServiceConnector = mscp.MockModelServiceConnector
ModelServiceConnectorPool = mscp.ModelServiceConnectorPool


class RecordingConnector(MockModelServiceConnector):
    def __init__(self) -> None:
        super().__init__("writer", capabilities={"zh", "writing"}, max_context_tokens=32000)
        self.started = asyncio.Event()
        self.stopped = asyncio.Event()
        self.block = False
        self.last_kwargs: dict[str, Any] = {}

    async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        self.last_kwargs = kwargs
        self.started.set()
        try:
            if self.block:
                await asyncio.Event().wait()
            return {
                "content": "answer",
                "usage": {"total_tokens": 4},
                "metadata": {"finish_reason": "stop"},
            }
        finally:
            self.stopped.set()

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[dict[str, Any]]:
        try:
            yield {"content": "first"}
            if self.block:
                self.started.set()
                await asyncio.Event().wait()
            yield {"content": "second"}
        finally:
            self.stopped.set()


def assemble(**adapter_kwargs: Any):
    connector = RecordingConnector()
    registry = InMemoryConnectorRegistry()
    registry.register(connector)
    pool = ModelServiceConnectorPool(registry)
    policy = InMemoryModelAccessPolicy()
    policy.set_role_requirement("writer", ModelCapabilityRequirement(required_tags={"zh"}))
    policy.set_task_requirement("draft", ModelCapabilityRequirement(required_tags={"writing"}))
    return ModelAccessObject(MSCPAdapter(pool, **adapter_kwargs), policy), pool, connector


@pytest.mark.asyncio
async def test_real_pool_is_adapted_and_parameters_and_results_are_preserved() -> None:
    mao, pool, connector = assemble()
    response = await mao.chat("writer-01", "writer", "draft", [], temperature=0.3)
    assert response.content == "answer"
    assert response.connector_id == "writer"
    assert response.model == "mock-model"
    assert response.usage == {"total_tokens": 4}
    assert response.metadata == {"finish_reason": "stop"}
    assert connector.last_kwargs == {"temperature": 0.3}
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_no_match_and_capacity_failure_are_exposed_as_mao_errors() -> None:
    mao, pool, _ = assemble()
    with pytest.raises(ModelAccessUnavailableError):
        await mao.chat(
            "writer-01",
            "writer",
            "draft",
            [],
            requirement=ModelCapabilityRequirement(required_tags={"vision"}),
        )
    async with pool.acquire("held", CapabilityRequirement()):
        with pytest.raises(ModelAccessBusyError):
            await mao.chat("writer-01", "writer", "draft", [])
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_acquisition_timeout_does_not_leak_capacity() -> None:
    mao, pool, _ = assemble(acquire_timeout=0.01)
    async with pool.acquire("held", CapabilityRequirement()):
        with pytest.raises(ModelAccessTimeoutError):
            await mao.chat("writer-01", "writer", "draft", [])
        assert pool.active_counts() == {"writer": 1}
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_invocation_timeout_stops_call_and_releases_lease() -> None:
    mao, pool, connector = assemble(invocation_timeout=0.01)
    connector.block = True
    with pytest.raises(ModelAccessTimeoutError):
        await mao.chat("writer-01", "writer", "draft", [])
    assert connector.stopped.is_set()
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_cancellation_propagates_and_releases_lease() -> None:
    mao, pool, connector = assemble()
    connector.block = True
    call = asyncio.create_task(mao.chat("writer-01", "writer", "draft", []))
    await connector.started.wait()
    call.cancel()
    with pytest.raises(asyncio.CancelledError):
        await call
    assert connector.stopped.is_set()
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_stream_is_normalized_and_closed_on_early_exit() -> None:
    mao, pool, connector = assemble()
    async with mao.stream("writer-01", "writer", "draft", []) as chunks:
        first = await anext(chunks)
        assert first.content == "first"
        assert first.connector_id == "writer"
        assert pool.active_counts() == {"writer": 1}
    assert connector.stopped.is_set()
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_stream_timeout_closes_generator() -> None:
    mao, pool, connector = assemble(invocation_timeout=0.01)
    connector.block = True
    with pytest.raises(ModelAccessTimeoutError):
        async with mao.stream("writer-01", "writer", "draft", []) as chunks:
            assert (await anext(chunks)).content == "first"
            await anext(chunks)
    assert connector.stopped.is_set()
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_stream_cancellation_propagates_and_closes_generator() -> None:
    mao, pool, connector = assemble()
    connector.block = True

    async def consume() -> None:
        async with mao.stream("writer-01", "writer", "draft", []) as chunks:
            async for _ in chunks:
                pass

    task = asyncio.create_task(consume())
    await connector.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert connector.stopped.is_set()
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_consumer_exception_is_preserved() -> None:
    mao, pool, connector = assemble()
    error = TimeoutError("business deadline")
    with pytest.raises(TimeoutError) as captured:
        async with mao.stream("writer-01", "writer", "draft", []) as chunks:
            await anext(chunks)
            raise error
    assert captured.value is error
    assert connector.stopped.is_set()
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_invalid_response_releases_lease() -> None:
    class InvalidConnector(RecordingConnector):
        async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
            return {"content": 12}

    registry = InMemoryConnectorRegistry()
    registry.register(InvalidConnector())
    pool = ModelServiceConnectorPool(registry)
    mao = ModelAccessObject(MSCPAdapter(pool))
    with pytest.raises(ModelAccessResponseError):
        await mao.chat("writer-01", "writer", "draft", [])
    assert pool.active_counts() == {}


@pytest.mark.asyncio
async def test_request_metadata_remains_in_access_layer() -> None:
    mao, pool, connector = assemble()
    response = await mao.chat("writer-01", "writer", "draft", [], metadata={"task_id": "task-1"})
    assert response.metadata["request_metadata"] == {"task_id": "task-1"}
    assert connector.last_kwargs == {}
    async with mao.stream(
        "writer-01", "writer", "draft", [], metadata={"task_id": "task-2"}
    ) as chunks:
        chunk = await anext(chunks)
        assert chunk.metadata["request_metadata"] == {"task_id": "task-2"}
    assert pool.active_counts() == {}
