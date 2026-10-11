# API Reference

## ModelCapabilityRequirement

```python
ModelCapabilityRequirement(
    required_tags: set[str] = set(),
    preferred_tags: set[str] = set(),
    min_context_tokens: int = 0,
    stream_required: bool = False,
)
```

Describes model capabilities required by a role or task.

## ModelAccessRequest

```python
ModelAccessRequest(
    agent_id: str,
    role: str,
    task_type: str,
    messages: list[dict[str, Any]],
    requirement: ModelCapabilityRequirement | None = None,
    metadata: dict[str, Any] = {},
)
```

Represents one model access request from an agent instance.

## ModelAccessResponse

```python
ModelAccessResponse(
    content: str,
    model: str | None = None,
    connector_id: str | None = None,
    usage: dict[str, Any] = {},
    metadata: dict[str, Any] = {},
)
```

Represents the normalized response returned to Agent Team code.

## InMemoryModelAccessPolicy

```python
policy = InMemoryModelAccessPolicy()
policy.set_role_requirement("writer", requirement)
policy.set_task_requirement("proposal_writing", requirement)
requirement = policy.resolve(role, task_type)
```

Maps agent roles and task types to model capability requirements.

## ModelAccessObject

```python
mao = ModelAccessObject(connector_pool, policy)

response = await mao.chat(
    agent_id="writer-01",
    role="writer",
    task_type="proposal_writing",
    messages=messages,
)
```

`ModelAccessObject` delegates connector acquisition and invocation to a
connector-pool-like object.
