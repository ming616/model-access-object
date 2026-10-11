from dataclasses import dataclass

from model_access_object import ModelAccessObject


@dataclass
class WriterAgent:
    agent_id: str
    mao: ModelAccessObject

    async def write(self, topic: str, draft: str = "", feedback: str = "") -> str:
        prompt = (
            f"Revise this draft: {draft}\nReview feedback: {feedback}"
            if feedback
            else f"Draft a project proposal about: {topic}"
        )
        response = await self.mao.chat(
            self.agent_id,
            "writer",
            "proposal_writing",
            [{"role": "user", "content": prompt}],
        )
        return response.content


@dataclass
class ReviewerAgent:
    agent_id: str
    mao: ModelAccessObject

    async def review(self, draft: str) -> str:
        response = await self.mao.chat(
            self.agent_id,
            "reviewer",
            "proposal_review",
            [
                {
                    "role": "system",
                    "content": "Review the draft. Return APPROVED or REVISION: followed by actionable feedback.",
                },
                {"role": "user", "content": draft},
            ],
        )
        return response.content.strip()


@dataclass
class ProposalResult:
    draft: str
    review: str
    revisions: int
    approved: bool


@dataclass
class ProposalTeam:
    writer: WriterAgent
    reviewer: ReviewerAgent
    max_revisions: int = 2

    async def run(self, topic: str) -> ProposalResult:
        if self.max_revisions < 0:
            raise ValueError("max_revisions must be non-negative.")
        draft = await self.writer.write(topic)
        for revision in range(self.max_revisions + 1):
            review = await self.reviewer.review(draft)
            if review == "APPROVED":
                return ProposalResult(draft, review, revision, True)
            if revision < self.max_revisions:
                draft = await self.writer.write(topic, draft, review)
        return ProposalResult(draft, review, self.max_revisions, False)
