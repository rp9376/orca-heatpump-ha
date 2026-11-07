# Contributing

Thanks for helping. Issues and pull requests are welcome; for anything
bigger than a fix, open an issue first.

## Development setup

The checks need Python 3.14, Home Assistant 2026.11 and the dev
dependencies; a Home Assistant core dev container works well:

```sh
pip install homeassistant pytest-homeassistant  # matching versions
pip install --group dev --group ci                # from pyproject.toml
pytest                     # tests, against the display emulator
prek run --all-files       # ruff, ruff format, mypy (strict), codespell
python -m script.hassfest --integration-path custom_components/orca_heatpump
```

Tests never talk to a real heat pump. They run Home Assistant against
`tools/emulator/`, which serves recorded data from `tests/fixtures/dumps/`.

## Layout

- `custom_components/orca_heatpump/client/` talks to the display and
  imports nothing from Home Assistant: `catalog.py` (every tag the
  integration reads or writes), `topology.py` (the 45 wiring schemas),
  `codec.py`, `protocol.py`, `client.py`.
- The rest of `custom_components/orca_heatpump/` is the Home Assistant
  integration: one module per platform, all built on `entity.py`.
- `docs/decisions/` records why things are the way they are.

## Adding a tag

1. Find the tag's meaning, type, scale, unit and range. Prefer the
   manufacturer's metadata; never guess a writable range.
2. Add a `TagDef` to `client/catalog.py` (and to `CATALOG` at the end).
   Circuit tags name the tag of each slot in `slot_tags`, because the
   display's names are irregular. Password and code tags never go in.
3. Only settings the display offers to users may be `writable`; installer
   settings stay read-only.
4. Add an entity description to the platform module, with a
   `translation_key` (by default the catalog key), and names in
   `strings.json`, `translations/en.json` (same content) and
   `translations/sl.json`. Add an icon in `icons.json` if the device class
   gives none.
5. Run the tests and update the snapshots
   (`pytest --snapshot-update`); review the snapshot diff.

`tests/client/test_catalog.py` checks the catalog against the display's tag
list and the manufacturer's metadata.

## Adding or fixing a translation

Translations live in `custom_components/orca_heatpump/translations/`.
`en.json` must equal `strings.json`, and every other language must have
exactly the same keys (a test checks both). To add a language, copy
`en.json` to `<language>.json` and translate the values.

## Adding a fixture

See [docs/supported-setups.md](docs/supported-setups.md#add-your-setup):
diagnostics downloads become fixtures with `tools/dump_to_fixture.py`.

## The dashboard

`docs/dashboard/` is generated: change `tools/build_dashboard.py` and run
`python -m tools.build_dashboard`. It uses built-in cards only, and only entities
that are enabled by default; a test checks both.

## Style

Python 3.14, Home Assistant's ruff settings, mypy strict, `@override` on
overrides. Comments say why, not what. One change per commit.
