# ATF / MAO / MSCP Prototype

The [ATF repository](https://github.com/ming616/Agent-Task-Framework) contains
the application composition and durable proposal Team example. Its business
Agent code imports MAO; composition code supplies MSCP and the task store.

| Component | Prototype responsibility |
| --- | --- |
| Business Team | Writer, evidence checklist, reviewer, bounded revision |
| ATF | Dependencies, work concurrency, context/history, SQLite checkpoints and resume |
| MAO | Access policy, model invocation, normalized value snapshot and correlation |
| MSCP | Capacity waiting, guarded leases and cancellation cleanup |

## Run

Clone all three repositories as siblings. From ATF's root, with an activated
Python 3.10+ environment:

```bash
pip install -e . -e ../model-access-object -e ../model-service-connector-pool
python -m examples.prototype --db proposal.sqlite create --task-id proposal-demo
python -m examples.prototype --db proposal.sqlite advance proposal-demo
python -m examples.prototype --db proposal.sqlite resume proposal-demo
```

The first execution process saves draft/evidence outputs and pauses. A new
process resumes at the review join, creates a revised draft after feedback,
and finishes. The service fixture is deterministic and offline.

## Checkpoint Correlation

```python
response = await mao.chat(
    agent_id=f"{task_id}:writer", role="writer", task_type="proposal",
    messages=messages,
    metadata={"task_id": task_id, "work_id": work_id, "attempt_id": attempt_id},
)
value = response.to_dict()
```

Correlation appears in `value["metadata"]["request_metadata"]`; it is not a
provider keyword argument. Caller-owned snapshots retain content, model,
connector, usage and metadata. Keep credentials in application configuration.
Custom backends must supply JSON-compatible values for ATF's JSON store.

## Verification and Boundaries

ATF's optional integration suite verifies two isolated tasks sharing one pool,
cancellation of active/waiting access, and recovery in separate CLI processes.
Run each repository's tests from its own root to avoid `examples` name clashes.

ATF recreates Agents after resume and supplies saved actor history. It owns
task state; MAO owns access; MSCP owns capacity. Shared services remain
application-owned. Unconfirmed external operations require explicit recovery
and business-side verification. The prototype uses a local SQLite store and
one event loop; a remote shared pool remains future work.

MAO 0.1.0 source in this revision includes `ModelAccessResponse.to_dict()`, used
by the ATF example. ATF's integration CI pins compatible companion commits.
