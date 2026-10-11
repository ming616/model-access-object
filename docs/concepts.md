# Concepts

## MAO

MAO means `Model Access Object`.

It is an application-facing model access layer for agentic systems. It plays a
role similar to DAO in traditional information systems.

## Responsibility

MAO should handle:

- role-to-model-capability mapping
- task-to-model-capability mapping
- model access request construction
- request and response normalization
- delegation to MSCP

MAO should not handle:

- low-level provider protocol details
- connector health checks
- connector leasing
- connector concurrency accounting
- model endpoint lifecycle

Those are MSCP responsibilities.

## Layering

```text
Task Entry
  -> Agent Team
  -> MAO
  -> MSCP
  -> ModelServiceConnector
  -> Model Service
```

## Key Boundary

Agent Team expresses business intent.

MAO translates business intent into model access requirements.

MSCP selects and leases concrete model service connectors.
