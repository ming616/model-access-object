# Concepts

## Responsibilities

Agent Team defines business goals, roles, collaboration, and feedback.
MAO defines how an Agent uses model services: access requirements, request
construction, ordinary or streaming invocation, and normalized results.
MSCP defines how available model resources are acquired and returned.

The optional MSCP adapter is part of MAO. It translates contracts and performs
access operations using MSCP's leases. Provider connectors implement wire
protocols below the resource boundary.

## Application-Owned Policy

A role-to-capability policy is access configuration supplied by the application.
It neither defines business roles nor assigns tasks. Policies combine hard
constraints before resource acquisition.

Business instructions, tools, feedback decisions, and collaboration graphs remain
with Agent Team. Independent memory and storage services supply persistent data.

## Runtime Objects

Roles are design-time definitions. Agent instances execute actual tasks and
receive MAO through constructor injection. Instances acquire no permanent model
binding. MAO borrows a lease for each access operation and returns it afterwards.

## Framework Direction

A larger framework can add common configuration, component composition, and
lifecycle management around these interfaces. Current examples use explicit
constructor injection. A general container is future work to be extracted from
application experience.
