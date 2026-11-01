"""A diagnostics download turns into a fixture the emulator replays."""

import json
from pathlib import Path

import pytest
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.diagnostics import get_diagnostics_for_config_entry
from pytest_homeassistant.typing import ClientSessionGenerator

from homeassistant.core import HomeAssistant
from tools.dump_to_fixture import convert, main
from tools.emulator import Emulator

from .conftest import serve


@pytest.mark.parametrize("pump", ["ours", "duo", "mono"], indirect=True)
async def test_round_trip(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
    tmp_path: Path,
) -> None:
    """The fixture made from diagnostics gives the same readings again."""
    coordinator = init_integration.runtime_data.coordinator
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, init_integration
    )
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(convert(diagnostics, "test", None)), encoding="utf-8")

    runner, host = await serve(Emulator.from_dump(path))
    try:
        coordinator.client._base = f"http://{host}"
        coordinator.client._token = None
        before = coordinator.data
        await coordinator.async_refresh()
    finally:
        await runner.cleanup()

    assert coordinator.last_update_success
    assert {t: (r.raw, r.value) for t, r in coordinator.data.readings.items()} == {
        t: (r.raw, r.value) for t, r in before.readings.items()
    }


def test_command_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The script converts a downloaded file and says what it wrote."""
    download = tmp_path / "diagnostics.json"
    download.write_text(
        json.dumps(
            {
                "data": {
                    "topology": {"schema": 7},
                    "tags": {
                        "2_Poti1": {"raw": "305", "reason": None},
                        "2_Poti2": {"raw": "-9999", "reason": "not_connected"},
                        "2_Temp_RF3": {"raw": None, "reason": "unknown_tag"},
                        "2_Poti3": {"raw": "E_FAIL", "reason": "tag_error"},
                        "2_Poti4": {"raw": None, "reason": "no_response"},
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "fixture.json"
    monkeypatch.setattr(
        "sys.argv",
        ["dump_to_fixture", str(download), str(output), "--description", "Mono"],
    )

    main()

    fixture = json.loads(output.read_text(encoding="utf-8"))
    assert fixture["schema"] == 7
    assert fixture["tags"] == {
        "2_Poti1": {"status": "S_OK", "value": "305"},
        "2_Poti2": {"status": "S_OK", "value": "-9999"},
        "2_Poti3": {"status": "E_FAIL"},
        "2_Temp_RF3": {"status": "E_UNKNOWNTAG"},
    }
    assert "schema 7, 4 tags" in capsys.readouterr().out
