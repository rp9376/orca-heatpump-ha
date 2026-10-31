# Architecture decision records

One file per decision: context, decision, consequences. "Accepted" means the
user decided; "Proposed" means a default from `PLAN.md` §3 or a new finding
that the user confirms at a checkpoint.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-integration-domain.md) | Domain `orca_heatpump` | Accepted 2026-10-30 |
| [0002](0002-repository-name.md) | Repository `orca-heatpump-ha` | Proposed (CP0) |
| [0003](0003-client-package-location.md) | Protocol client inside the integration, HA-independent | Proposed (CP0) |
| [0004](0004-tag-catalog-format.md) | Tag catalog as typed Python | Proposed (CP0) |
| [0005](0005-no-runtime-dependencies.md) | No runtime dependencies | Proposed (CP0) |
| [0006](0006-minimum-home-assistant-version.md) | Minimum Home Assistant 2026.11.0 | Proposed (CP0) |
| [0007](0007-polling.md) | One coordinator, 30 s | Proposed (CP0) |
| [0008](0008-no-migration.md) | No migration from orca-energy-ha | Accepted 2026-10-30 |
| [0009](0009-brand-icon.md) | Neutral heat pump brand icon | Proposed (CP0) |
| [0010](0010-entity-model.md) | Entity model | Proposed (finalised at CP1) |
| [0011](0011-test-plugin.md) | Test with HA's pytest-home-assistant, from the core tag | Proposed (CP0) |
