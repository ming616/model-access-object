import asyncio
from typing import Any

from model_service_connector_pool import (
    InMemoryConnectorRegistry,
    MockModelServiceConnector,
    ModelServiceConnectorPool,
)
from proposal_team import ProposalTeam, ReviewerAgent, WriterAgent

from model_access_object import (
    InMemoryModelAccessPolicy,
    ModelAccessObject,
    ModelCapabilityRequirement,
    MSCPAdapter,
)


class DemoConnector(MockModelServiceConnector):
    """An offline service stub with deterministic draft and review responses."""

    async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(0)
        prompt = messages[-1]["content"]
        if "review" in self.metadata.capabilities:
            content = (
                "APPROVED"
                if prompt.startswith("Revised draft")
                else "REVISION: Add an evaluation plan."
            )
        else:
            content = (
                "Revised draft with an evaluation plan."
                if prompt.startswith("Revise")
                else "Initial draft."
            )
        return {"content": content, "model": self.metadata.model}


def assemble() -> tuple[ModelServiceConnectorPool, ModelAccessObject]:
    registry = InMemoryConnectorRegistry()
    registry.register(
        DemoConnector("writing-service", capabilities={"zh", "writing"}, max_context_tokens=32000)
    )
    registry.register(
        DemoConnector("review-service", capabilities={"zh", "review"}, max_context_tokens=32000)
    )
    pool = ModelServiceConnectorPool(registry)
    policy = InMemoryModelAccessPolicy()
    policy.set_role_requirement(
        "writer", ModelCapabilityRequirement(required_tags={"zh", "writing"})
    )
    policy.set_role_requirement(
        "reviewer", ModelCapabilityRequirement(required_tags={"zh", "review"})
    )
    return pool, ModelAccessObject(MSCPAdapter(pool, acquire_timeout=5), policy)


async def main() -> None:
    pool, mao = assemble()
    async with pool:
        teams = [
            ProposalTeam(
                WriterAgent(f"writer-{index}", mao), ReviewerAgent(f"reviewer-{index}", mao)
            )
            for index in range(2)
        ]
        results = await asyncio.gather(*(team.run("Shared model services") for team in teams))
        for index, result in enumerate(results):
            print(
                f"team-{index}: approved={result.approved}, revisions={result.revisions}, draft={result.draft}"
            )
        print("Active leases after both teams:", pool.active_counts())


if __name__ == "__main__":
    asyncio.run(main())
