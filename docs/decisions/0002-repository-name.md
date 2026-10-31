# 0002. Repository name `orca-heatpump-ha`

Status: Accepted (user, 2026-10-31)

## Context
The repository will be public under the user's GitHub account (rp9376).
For now it is local only, with no remote (user, 2026-10-31).
HACS installs from a repository; its name is what users see when adding a
custom repository.

## Decision
The repository is `orca-heatpump-ha`, at `github.com/rp9376/orca-heatpump-ha`.

## Consequences
- The name says what it is and mirrors the domain (ADR 0001); the domain
  does not depend on it.
- `manifest.json` `documentation` and `issue_tracker` point there. Changing
  the name later means updating both.
