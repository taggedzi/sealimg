# 0005 - Work Management Through GitHub Issues

- Status: Accepted
- Date: 2026-03-06

## Context
Sealimg has an implementation TODO and milestone roadmap but no execution tracker tied to development flow.

## Decision
Use GitHub Issues (epics + child tasks) as the primary implementation tracking system.

## Consequences
- Work can be prioritized, assigned, and reviewed with traceable acceptance criteria.
- Decisions and implementation tasks remain linked via issue references and ADRs.
- Requires initial setup of labels/milestones/templates in the repository.

## Alternatives Considered
- Track only in `TODO.md`: low overhead but weaker ownership/dependency tracking.
- External project management tool: more capability, but additional process/tooling overhead.
