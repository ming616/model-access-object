import asyncio
from typing import Any

from model_access_object import (
    InMemoryModelAccessPolicy,
    ModelAccessObject,
    ModelAccessResponse,
    ModelCapabilityRequirement,
)


class MockConnectorPool:
    async def invoke_with_requirement(
        self,
        agent_id: str,
        requirement: ModelCapabilityRequirement,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ModelAccessResponse:
        return ModelAccessResponse(
            content=f"[{agent_id}] {messages[-1]['content']}",
            model="mock-model",
            connector_id="mock-connector",
            metadata={
                "required_tags": sorted(requirement.required_tags),
                "min_context_tokens": requirement.min_context_tokens,
            },
        )


async def main() -> None:
    policy = InMemoryModelAccessPolicy()
    policy.set_role_requirement(
        "writer",
        ModelCapabilityRequirement(
            required_tags={"zh", "writing"},
            preferred_tags={"long-context"},
            min_context_tokens=16_000,
        ),
    )

    mao = ModelAccessObject(MockConnectorPool(), policy)
    response = await mao.chat(
        agent_id="proposal-writer-01",
        role="writer",
        task_type="proposal_writing",
        messages=[{"role": "user", "content": "Draft the project summary."}],
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
