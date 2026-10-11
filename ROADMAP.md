# Roadmap

## Principle

Agent Team owns business logic. MAO owns model service access. MSCP owns
resource acquisition and release.

## Available

- Access request and normalized response contracts.
- Combination of role, task, and explicit capability requirements.
- Ordinary and context-managed streaming access.
- MSCP adapter with acquisition and invocation timeouts.
- Access errors and preserved request metadata.
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
- Define framework lifecycle boundaries for Agents, MAO, and shared resources.

No new framework repository, package release, or source archive is scheduled
in this phase.
