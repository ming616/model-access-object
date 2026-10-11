# Usage Guide

## Source Setup

Clone MAO and MSCP as sibling repositories. Use source paths while developing:

```bash
PYTHONPATH=src:../model-service-connector-pool/src python examples/layered_team.py
```

The core example requires only Python 3.10 or newer. Source development can also
use `pip install -e ../model-service-connector-pool` and `pip install -e .`.
No published distribution is required.

## CI and Paired Tests

MAO's unit tests run independently. Without the companion source, pytest reports
the MSCP integration module as skipped. With the source path above, the full suite
includes the paired integration tests.

The optional CI integration job pins a compatible MSCP commit. Set repository
variable `ENABLE_MSCP_INTEGRATION=true` to enable it. When the companion repository
is private, provide secret `MSCP_READ_TOKEN` with read access to that repository.
The default Actions token does not grant access to another private repository. The
integration job runs on trusted pushes or manual dispatch, not pull requests.

## Composition and Injection

Configure a registry and one MSCP pool in application startup code. Create an
access policy, construct MAO around `MSCPAdapter(pool)`, and inject MAO into
Agent instances. Complete Agent tasks before closing the pool.

```python
policy = InMemoryModelAccessPolicy()
policy.set_role_requirement(
    "writer",
    ModelCapabilityRequirement(required_tags={"zh", "writing"}, min_context_tokens=16000),
)
mao = ModelAccessObject(MSCPAdapter(pool, acquire_timeout=5), policy)
writer = WriterAgent(agent_id="writer-01", mao=mao)
```

Capabilities describe access needs. Agent Team decides each role's business
behavior and supplies the task messages.

## Business Collaboration

`examples/proposal_team.py` defines writer/reviewer instances and the feedback
cycle. It imports MAO only. Review results decide whether the writer revises;
the Team limits revision rounds.

`examples/layered_team.py` contains composition and deterministic service stubs.
Two teams share the same pool through injected MAO. It demonstrates concurrency
and resource reuse; its generated text is an offline fixture.

## Ordinary and Streaming Access

```python
response = await mao.chat(
    "writer-01", "writer", "proposal_writing",
    [{"role": "user", "content": "Draft the introduction."}],
    metadata={"task_id": "task-1"},
    temperature=0.2,
)
```

```python
async with mao.stream("writer-01", "writer", "proposal_writing", messages) as chunks:
    async for chunk in chunks:
        print(chunk.content, end="")
```

Keep stream processing in its context. Early exit, exceptions, and cancellation
close the provider stream and return the slot. Business code can handle MAO's
availability, capacity, and timeout errors.

## Actual Endpoint

Install the optional transport in the sibling MSCP repository:

```bash
pip install -e "../model-service-connector-pool[http]"
export MODEL_SERVICE_BASE_URL=http://localhost:8000/v1
export MODEL_SERVICE_MODEL=your-served-model
PYTHONPATH=src:../model-service-connector-pool/src python examples/openai_compatible.py
```

Set `MODEL_SERVICE_API_KEY` in the environment when the service requires
authentication. Configure context size, tags, and capacity to match the actual
service before using it in a Team.

## Memory and Deployment

The application or a separate memory service stores history and supplies context
for each call. Sessions can outlive resource leases.

Embedded sharing requires the same pool instance in one event loop. Multiple
applications will use a future centrally hosted MSCP through a remote MAO
adapter. These deployments preserve the same business-facing access boundary.
