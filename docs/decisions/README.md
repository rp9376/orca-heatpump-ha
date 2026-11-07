# Architecture decision records

One file per decision: context, decision, consequences. "Accepted" means the
user decided; "Proposed" means a default from `PLAN.md` §3 or a new finding
that the user confirms at a checkpoint. `PLAN.md` is the project's original plan and
`docs/progress.md` its working log.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-integration-domain.md) | Domain `orca_heatpump` | Accepted 2026-10-30 |
| [0002](0002-repository-name.md) | Repository `orca-heatpump-ha`, local only for now | Accepted 2026-10-31 |
| [0003](0003-client-package-location.md) | Protocol client inside the integration, HA-independent | Accepted 2026-10-31 |
| [0004](0004-tag-catalog-format.md) | Tag catalog as typed Python | Accepted 2026-10-31 |
| [0005](0005-no-runtime-dependencies.md) | No runtime dependencies | Accepted 2026-10-31 |
| [0006](0006-minimum-home-assistant-version.md) | Minimum Home Assistant 2026.11.0; latest HA only, no backward compatibility | Accepted 2026-10-31 |
| [0007](0007-polling.md) | One coordinator, 30 s | Accepted 2026-10-31 |
| [0008](0008-no-migration.md) | No migration from orca-energy-ha | Accepted 2026-10-30 |
| [0009](0009-brand-icon.md) | Official Orca logo as the brand icon | Accepted 2026-10-31 |
| [0010](0010-entity-model.md) | Entity model (`docs/entity-model.md`) | Accepted 2026-11-01 |
| [0011](0011-test-plugin.md) | Test with HA's pytest-home-assistant, from the core tag | Accepted 2026-10-31 |
| [0012](0012-power-limits-opt-in.md) | Power limits are an opt-in, guarded setting | Accepted 2026-11-01 |
| [0013](0013-no-network-discovery.md) | No network discovery | Accepted 2026-11-01 |
| [0014](0014-no-topology-overrides.md) | No topology overrides | Accepted 2026-11-07 |
