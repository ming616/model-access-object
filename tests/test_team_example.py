from typing import Any

import pytest

from examples.proposal_team import ProposalTeam, ReviewerAgent, WriterAgent
from model_access_object import ModelAccessResponse


class ScriptedAccess:
    def __init__(self, approved: bool) -> None:
        self.approved = approved
        self.calls: list[tuple[str, str]] = []
        self.review_count = 0

    async def chat(
        self, agent_id: str, role: str, task_type: str, messages: list[dict[str, Any]]
    ) -> ModelAccessResponse:
        self.calls.append((role, messages[-1]["content"]))
        if role == "writer":
            return ModelAccessResponse(content="draft")
        self.review_count += 1
        return ModelAccessResponse(
            content="APPROVED"
            if self.approved and self.review_count > 1
            else "REVISION: Add evidence."
        )


@pytest.mark.asyncio
async def test_business_team_uses_injected_model_access_and_feedback() -> None:
    mao = ScriptedAccess(approved=True)
    team = ProposalTeam(WriterAgent("writer-01", mao), ReviewerAgent("reviewer-01", mao))
    result = await team.run("project topic")
    assert result.approved
    assert result.revisions == 1
    assert [role for role, _ in mao.calls] == ["writer", "reviewer", "writer", "reviewer"]
    assert "Add evidence." in mao.calls[2][1]


@pytest.mark.asyncio
async def test_business_feedback_has_a_defined_revision_limit() -> None:
    mao = ScriptedAccess(approved=False)
    team = ProposalTeam(
        WriterAgent("writer-01", mao), ReviewerAgent("reviewer-01", mao), max_revisions=1
    )
    result = await team.run("project topic")
    assert not result.approved
    assert result.revisions == 1
    assert mao.review_count == 2
