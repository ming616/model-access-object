# Roadmap

## Principle

Agent Team owns business logic. MAO owns model service access. MSCP owns
resource acquisition and release.

## Available

- Access request and normalized response contracts.
- Combination of role, task, and explicit capability requirements.
- Ordinary and context-managed streaming access.
- MSCP adapter with acquisition and invocation timeouts.
- Access errors, preserved request metadata, and detached response snapshots.
- Deep request metadata snapshots, including event correlation across capacity waits and chunks.
- Integration with ATF task checkpoints and Agent scopes.
- Independent business-only Agent classes and bounded feedback example.
- Two teams sharing one embedded pool.
- An environment-configured HTTP endpoint example.

## Next: Validate Real Applications

- Exercise the access contract against deployed local model services.
- Keep business prompts and collaboration in application repositories.
- Refine structured output and tool-call access contracts from actual use.
- Add optional source integration instructions for additional backends.

## Next: Shared Service and Framework Composition

- Add a remote adapter when MSCP's institutional shared service is defined.
- Extract common configuration and composition from multiple applications.
- Validate ATF lifecycle boundaries for Agents, MAO, and shared resources.

ATF is now the companion framework repository. Package index releases and
source archives have not been published in this phase.
