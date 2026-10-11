from contextlib import asynccontextmanager
from typing import Any

import pytest

from model_access_object import (
    InMemoryModelAccessPolicy,
    ModelAccessObject,
    ModelAccessResponse,
    ModelCapabilityRequirement,
)


class RecordingConnectorPool:
    def __init__(self) -> None:
        self.last_requirement: ModelCapabilityRequirement | None = None

    async def invoke_with_requirement(
        self,
        agent_id: str,
        requirement: ModelCapabilityRequirement,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ModelAccessResponse:
        self.last_requirement = requirement
        return ModelAccessResponse(content=messages[-1]["content"])


@pytest.mark.asyncio
async def test_mao_resolves_role_requirement() -> None:
    pool = RecordingConnectorPool()
    policy = InMemoryModelAccessPolicy()
    policy.set_role_requirement(
        "writer",
        ModelCapabilityRequirement(required_tags={"zh", "writing"}, min_context_tokens=16000),
    )
    mao = ModelAccessObject(pool, policy)

    response = await mao.chat(
        agent_id="agent-1",
        role="writer",
        task_type="proposal_writing",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.content == "hello"
    assert pool.last_requirement is not None
    assert pool.last_requirement.required_tags == {"zh", "writing"}
    assert pool.last_requirement.min_context_tokens == 16000


def test_role_task_and_explicit_hard_constraints_are_combined() -> None:
    policy = InMemoryModelAccessPolicy()
    role = ModelCapabilityRequirement(required_tags={"zh"}, min_context_tokens=16000)
    policy.set_role_requirement("writer", role)
    policy.set_task_requirement("draft", ModelCapabilityRequirement(required_tags={"writing"}))
    result = policy.resolve(
        "writer",
        "draft",
        ModelCapabilityRequirement(required_tags={"offline"}, stream_required=True),
    )
    assert result.required_tags == {"zh", "writing", "offline"}
    assert result.min_context_tokens == 16000
    assert result.stream_required
    assert role.required_tags == {"zh"}


@pytest.mark.asyncio
async def test_access_metadata_is_returned_with_a_custom_backend() -> None:
    mao = ModelAccessObject(RecordingConnectorPool())
    response = await mao.chat(
        "agent",
        "writer",
        "draft",
        [{"role": "user", "content": "hello"}],
        metadata={"task": "task-1"},
    )
    assert response.metadata["request_metadata"] == {"task": "task-1"}


@pytest.mark.asyncio
async def test_custom_stream_backend_receives_requirement_and_closes_on_exit() -> None:
    class Backend(RecordingConnectorPool):
        closed = False

        @asynccontextmanager
        async def stream_with_requirement(self, agent_id, requirement, messages, **kwargs):
            self.last_requirement = requirement

            async def chunks():
                yield ModelAccessResponse(content="first")
                yield ModelAccessResponse(content="second")

            try:
                yield chunks()
            finally:
                self.closed = True

    backend = Backend()
    mao = ModelAccessObject(backend)
    async with mao.stream("agent", "writer", "draft", [], metadata={"task": "task-2"}) as chunks:
        chunk = await anext(chunks)
        assert chunk.content == "first"
        assert chunk.metadata["request_metadata"] == {"task": "task-2"}
    assert backend.last_requirement.stream_required
    assert backend.closed


@pytest.mark.asyncio
async def test_streaming_is_explicitly_unsupported_by_chat_only_backend() -> None:
    mao = ModelAccessObject(RecordingConnectorPool())
    with pytest.raises(NotImplementedError):
        async with mao.stream("agent", "writer", "draft", []):
            pass
