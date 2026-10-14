# API Reference

## Data Objects

`ModelCapabilityRequirement(required_tags=set(), preferred_tags=set(),
min_context_tokens=0, stream_required=False)` describes access requirements.
Negative context sizes raise `ValueError`.

`ModelAccessRequest(agent_id, role, task_type, messages,
requirement=None, metadata={})` describes one access request.

`ModelAccessResponse(content, model=None, connector_id=None,
usage={}, metadata={})` is returned for ordinary calls and for each stream chunk.
Streaming content is a delta; concatenate content to assemble text.

`response.to_dict()` produces a detached dataclass value snapshot, including
nested usage and metadata. ATF or the application can save this value in a
checkpoint. The response object does not store history itself. Custom metadata
must be JSON-compatible if the caller intends to persist it as JSON.

Request metadata stays in the access layer. When provided, it is copied into
response metadata under `request_metadata`; it is not sent as a provider
parameter.

## InMemoryModelAccessPolicy

```python
policy.set_role_requirement("writer", requirement)
policy.set_task_requirement("proposal_writing", requirement)
resolved = policy.resolve(role, task_type, explicit=None)
```

All applicable requirements are combined. Required and preferred tags use set
union, minimum context uses the maximum, and streaming uses logical OR. Explicit
requirements add constraints and cannot silently erase role or task constraints.
If no requirements are configured, the result is unconstrained.

Policies configure access needs for application-defined roles and tasks.
Agent creation, role assignment, collaboration, and feedback belong to Agent Team.

## ModelAccessObject

`ModelAccessObject(connector_pool, policy=None)` accepts an injected access
backend. The original `ModelConnectorPoolLike` protocol remains available in
`model_access_object.mao` for custom backends.

```python
response = await mao.chat(
    agent_id, role, task_type, messages,
    requirement=None, metadata=None, temperature=0.2,
)
response = await mao.execute(request, temperature=0.2)

async with mao.stream(
    agent_id, role, task_type, messages,
    requirement=None, metadata=None,
) as chunks:
    async for chunk in chunks:
        print(chunk.content)
```

Remaining keyword arguments are provider access parameters. Streaming
automatically requires a streaming-capable connector. Keep iteration inside its
context manager so early exit closes the stream and returns capacity.

## MSCPAdapter

`MSCPAdapter(pool, *, acquire_timeout=0, invocation_timeout=None)` adapts
`ModelServiceConnectorPool` to MAO's backend contract.

- Acquisition timeout zero fails immediately when matching resources are full.
- Positive acquisition timeout waits with a deadline; None allows cancellable waiting.
- Invocation timeout limits ordinary calls and each wait for a stream chunk.
- None disables the adapter's invocation timeout; transport timeouts still apply.

The adapter converts capability fields, invokes through a lease, and normalizes
content, model ID, connector ID, usage, and metadata. It uses the allocated
connector ID as resource attribution.

The adapter exposes `invoke_with_requirement(...)` and
`stream_with_requirement(...)` for backend integration. Most applications
call through MAO instead.

## Errors

| Error | Meaning |
| --- | --- |
| `ModelAccessUnavailableError` | No matching usable service, or a closed pool |
| `ModelAccessBusyError` | Matching service capacity is full |
| `ModelAccessTimeoutError` | Acquisition or invocation timed out |
| `ModelAccessResponseError` | Output violates the normalized response contract |
| `ModelAccessError` | Known provider request or response failure |

All derive from `ModelAccessError(RuntimeError)`; timeout also derives from
`TimeoutError`. Underlying exceptions are retained as causes. Cancellation and
business exceptions propagate without being converted into access failures.
## Request metadata isolation

MAO captures a deep snapshot of request metadata before waiting for a backend.
Streaming captures metadata at context entry and gives each chunk its own copy.
Nested caller or chunk mutations cannot alter another response's correlation
values. Applications may include task/work/attempt and human event identifiers;
MAO does not interpret approval decisions or persist events.
