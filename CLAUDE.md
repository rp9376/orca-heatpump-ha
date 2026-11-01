# Agent rules for orca-heatpump-ha

`PLAN.md` is the master plan; its §2 (ground rules) and §10 (write safety)
win over anything here. This file is the short version. Current state:
`docs/progress.md`. Decisions: `docs/decisions/`.

## Workspace

- Stay inside `~/WorkDir/Home_Assistant_ORCA_HA/`. Temporary files go in
  the session scratchpad or `.scratch/` (gitignored).
- Read-only: `../orca-energy-ha/` (the user's uncommitted work lives
  there), `../HAcore/` source, `../Citcuit_schemas.md`,
  `../ORCA_FIX_NOTES.md`.
- Yours to change: this repo, `../ha-dev/`, the dev HA state in
  `../HAcore/config/` (through the HA API, not `.storage/` edits), and the
  Work log in `../README.md`.
- No backups or leftover copies of old state.
- Never copy the dev HA login from `../README.md` into this repo; it
  becomes public.

## The heat pump is a real, fragile device

It heats a real house. Address and login are in `PLAN.md` §2.2.

- **Only the lead agent talks to the pump.** Subagents and tests use the
  recorded fixtures and the emulator (`tools/emulator/`).
- The pump allows only a few concurrent sessions. Before a research
  session, make sure no HA instance you control is polling it.
- Log in once, do all planned reads, and always call `cgi/logout` in a
  `finally`. Never run two pump sessions at once.
- On `#E_TOO_MANY_USERS`: wait 1, 2, 4, 8 minutes, then stop and ask the
  user. Never retry faster, never loop.
- Endpoints: only the allowlist in `PLAN.md` §2.2. `cgi/writeTags` only
  in Phase 6 with the user present and agreeing in the conversation.
  Never call anything on the "never call" list, not even to see what it
  returns.
- `cgi/readFile` (R14 only): one file per request, serially, paths from the
  protocol analysis or a directory listing, saved to
  `research/captures/readfile/`. Stop at the first unexpected error.
- The API drops records. Never conclude a tag is missing from one read.
- Record every live response you rely on in `research/captures/`.

## Data hygiene

- `research/captures/` is gitignored: raw captures contain MAC, IP,
  serial numbers and personal data. Commit only sanitised derivatives
  (placeholders for MAC/IP/serial).
- Passwords are not this integration's business: no password or code tag
  (name contains `GESLO`, `KODA` or `KODE`) goes into the catalog, and
  fixtures redact them.
- Manufacturer manuals: extract facts only, never copy text.

## Writes

- Product code writes only through `OrcaClient.async_write`: catalog
  writable tags, range-checked, skipped when unchanged, read back.
- Installer settings (`PLAN.md` §10) are never writable.
- Tests write to the emulator only.

## Code

- Python 3.14, no runtime dependencies beyond HA.
- Latest Home Assistant only (ADR 0006): use the newest APIs, never write
  compatibility code for older releases, raise the minimum in `hacs.json`
  when needed. The ha-dev container may move to any HA version we need.
- `custom_components/orca_heatpump/client/` never imports `homeassistant`.
- Follow `../HAcore/CLAUDE.md` and
  `../HAcore/.claude/skills/ha-integration-knowledge/`. Comments say why,
  not what. `@override` on overrides.
- Must pass: `ruff`, `ruff format`, `mypy` (strict), `pytest`, hassfest.
- Tests first for the client and topology; snapshot tests for platforms.
- Run checks in the dev container:
  `../ha-dev/ha-dev.sh test`, `../ha-dev/ha-dev.sh lint`,
  `../ha-dev/ha-dev.sh hassfest`.

## Process

- Work autonomously between checkpoints (CP0–CP3, `PLAN.md` §2.3). At a
  checkpoint, write the report in `docs/progress.md` and stop.
- Also stop when something contradicts the plan or would break a rule.
- One local commit per finished task. Local only: no remote repositories
  for now. Nothing is pushed or published, and no issues, PRs or comments
  are made, before CP3.
- Keep state on disk (`docs/progress.md`, `research/`, ADRs, the Status
  line in `PLAN.md`) so a fresh session can resume.
- Report faithfully: failures, skipped steps and unverified claims go in
  `docs/progress.md`.
