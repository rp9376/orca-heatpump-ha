# Supported setups

The heat pump's controller knows 45 wiring schemas: combinations of up to
three heating circuits (mixing or direct), hot water and solar collectors. A
buffer tank and a room sensor per circuit come on top. The integration reads
the schema and builds its devices from it.

## What is tested

| Setup | How |
|---|---|
| Duo 300 Solar, schema 23 (direct circuit 1, mixing circuit 2, hot water, solar), firmware 61 (2016-12-12), Mitsubishi outdoor unit | Live, read-only, and from two recorded dumps (idle and heating) |
| Duo, schema 3 (direct circuit 1 with a room sensor, hot water) | Recorded dump |
| Mono, schema 7 (direct circuits 1 and 2 with room sensors, hot water, buffer tank) | Recorded dump |
| Schema 43 (mixing circuits 1 and 2, direct circuit 3, hot water, buffer tank, room-regulated circuit 1) | Synthetic, from our dump with changed values |
| Schema 11 (one mixing circuit, nothing else) | Synthetic |
| All 45 schemas | Synthetic: each sets up, is detected as stored and gets one device per element |

Faults the display can produce (lost connection, refused logins, expired
sessions, dropped records, malformed answers, values nobody has seen yet)
are tested against an emulator of the display (`tools/emulator/`).

Writes were tested live on the Duo 300 Solar with the system switched off: 65
settings, each changed by one step, read back and restored. See
`docs/phase6-write-test-plan.md` for what was left out.

Not tested live yet: a pump with a room sensor, cooling in operation, a third
heating circuit, a buffer tank, and the writes left out of that test.

## Add your setup

If your pump has a setup or firmware that isn't listed, its data helps.

1. In Home Assistant, open the heat pump device, choose **⋮ → Download
   diagnostics**. The display's address and login are removed from the
   file; it holds your pump's settings and readings, nothing personal.
2. Open an issue with the file attached, and say which model you have,
   what is connected (heating circuits, hot water, solar, buffer tank, room
   sensors) and anything that looks wrong in Home Assistant.

A maintainer turns the file into a test fixture:

```sh
python -m tools.dump_to_fixture diagnostics.json \
    tests/fixtures/dumps/schemaN_model_YYYY-MM-DD.json \
    --description "Orca …, schema N (…)" --captured YYYY-MM-DDTHH:MM
```

and adds the pump to the platform tests (`PUMPS` in
`tests/components/orca_heatpump/conftest.py`).
