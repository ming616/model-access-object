# Usage Guide

## Define Role Policies

```python
from model_access_object import InMemoryModelAccessPolicy, ModelCapabilityRequirement

policy = InMemoryModelAccessPolicy()
policy.set_role_requirement(
    "writer",
    ModelCapabilityRequirement(
        required_tags={"zh", "writing"},
        preferred_tags={"long-context"},
        min_context_tokens=16000,
    ),
)
```

## Create MAO

```python
mao = ModelAccessObject(connector_pool, policy)
```

The `connector_pool` can be an adapter around MSCP.

## Use MAO From Agent Team

```python
response = await mao.chat(
    agent_id="proposal-writer-01",
    role="writer",
    task_type="proposal_writing",
    messages=[{"role": "user", "content": "Draft the project summary."}],
)
```

Agent Team code does not need to know which concrete model endpoint is used.

## Run Example

```bash
PYTHONPATH=src python examples/basic_usage.py
```
