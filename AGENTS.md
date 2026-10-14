# Model Access Object workspace conventions

These instructions cover this repository tree. Cross-component goals, task cards,
integrated baselines and review guidance live in the sibling repository
`../agentic-stack`; read its `AGENTS.md`, `docs/README.md` and the selected task card
before changing cross-component behaviour. Implementation work additionally follows
`../agentic-stack/docs/handoff.local-model.zh-CN.md`.

## Boundaries

- MAO builds requests, combines role, task and capability requirements, invokes through an
  injected backend and returns normalized results. It does not schedule tasks, open task
  databases or own capacity bookkeeping.
- Do not import `agent_task_framework`: task state, checkpoints and recovery belong to ATF.
- MSCP is reached through the adapter and the pool-like backend protocol only. A borrowed
  lease is used for one operation and returned on success, failure, cancellation, timeout
  and waiting paths alike.
- Prompts, roles, business rules and completion conditions stay with the business Team;
  access configuration describes capabilities, never roles.
- `pyproject.toml` keeps `dependencies = []`; provider-specific code belongs in adapters
  or optional extras.
- Response snapshots handed to callers are detached copies; nested request metadata must
  stay isolated across capacity waits and streamed chunks.

## Verification

```bash
pip install -e ".[dev]"
ruff check --config pyproject.toml src tests examples
pytest                                      # currently 22 tests
```

- `tests/test_mscp_integration.py` requires the MSCP checkout:
  `pip install -e ../model-service-connector-pool`.
- ATF and MAO both ship an `examples` package; never collect both in one pytest process.

## Change flow

- Commit in this repository. Never stage component sources from `../agentic-stack`.
- Push to both mirrors configured for `origin` (Gitee and GitHub) and confirm the commit
  is visible on both; GitHub access from the Windows workstation is intermittent and may
  need retries. Never force push.
- Record the compatible commit in `../agentic-stack/components.lock.json` only after both
  mirrors carry it, then run `python ../agentic-stack/scripts/workspace.py test` on clean
  checkouts.
- Cross-repository integration jobs in `.github/workflows/ci.yml` pin compatible sibling
  commits; refresh those pins when the overall lock moves.
- Report evidence per section 7 of `../agentic-stack/docs/handoff.local-model.zh-CN.md`
  and write it to `../agentic-stack/docs/reports/<task>-<date>.md`.
- Keep public contracts and access semantics stable unless a task card or ADR authorises
  the change.
