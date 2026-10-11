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
