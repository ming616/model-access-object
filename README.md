# Model Access Object

MAO provides model service access for Agent Teams.

| Layer | Responsibility |
| --- | --- |
| Agent Team | Business tasks, role collaboration, and feedback |
| ATF | Task execution, context checkpoints, dependency scheduling, and recovery |
| MAO | Request construction, invocation style, and normalized results |
| MSCP | Model resource acquisition and release |
| Connector | Provider protocol adaptation |

This follows the separation used by service objects, DAOs, and connection pools
in layered applications. Business prompts and collaboration remain with Agent
Team. Access configuration describes capabilities; it does not define roles.

## Current Core

- Model access requests and normalized responses.
- Combination of role, task, and explicit capability requirements.
- Ordinary and streaming access through an injected backend.
- An MSCP adapter that borrows, uses, and returns guarded leases.
- Access-layer errors for resource availability, capacity, and timeouts.
- Detached response snapshots for caller-owned task checkpoints.
- A business-only team example with a bounded review/revision feedback cycle.

## Access

```python
from model_access_object import ModelAccessObject, MSCPAdapter

mao = ModelAccessObject(MSCPAdapter(pool, acquire_timeout=5))
response = await mao.chat(
    agent_id="writer-01",
    role="writer",
    task_type="proposal_writing",
    messages=[{"role": "user", "content": "Draft the project summary."}],
)
```

The application composition code constructs the pool, MAO, and Agent instances.
Agents receive MAO through their constructors. Success, errors, cancellation,
and early stream closure all return the borrowed capacity.

## Run From Source

Clone this repository and
[model-service-connector-pool](https://github.com/ming616/model-service-connector-pool)
as sibling directories. From this repository:

```bash
PYTHONPATH=src:../model-service-connector-pool/src python examples/layered_team.py
```

This offline demo runs two teams against the same pool. Each writer receives
review feedback and produces a revision. The final active lease count is empty.
For an actual configured endpoint, see `examples/openai_compatible.py`.

## Documentation

- [Layered Architecture (Chinese)](docs/architecture.zh-CN.md)
- [Concepts](docs/concepts.md)
- [Usage Guide](docs/usage.md)
- [API Reference](docs/api.md)
- [Roadmap](ROADMAP.md)

## Development

```bash
pip install -e ".[dev]"
ruff check --config pyproject.toml .
PYTHONPATH=src:../model-service-connector-pool/src pytest
```

The companion [Agent Task Framework](https://github.com/ming616/Agent-Task-Framework)
provides a task runtime and Agent scopes. Its proposal prototype combines
parallel work, dependency joins, bounded feedback, and SQLite recovery with MAO
and MSCP. See [the three-project guide](docs/framework-prototype.md).

MSCP remains an embedded pool for one asyncio event loop; an institutional
shared service is future work.

CI runs MAO's independent tests on Python 3.10, 3.11, and 3.12. MSCP integration
tests run locally when the paired source is on the Python path. The optional
cross-repository CI job is configured separately; see the usage guide.

## License

Apache-2.0
