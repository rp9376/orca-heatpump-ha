"""Home Assistant finds the integration in this repository."""

from custom_components.orca_heatpump.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration


async def test_integration_is_discovered(hass: HomeAssistant) -> None:
    """The integration loads as a custom integration without requirements."""
    integration = await async_get_integration(hass, DOMAIN)

    assert not integration.is_built_in
    assert integration.manifest["codeowners"] == ["@rp9376"]
    # No runtime dependencies beyond Home Assistant (ADR 0005).
    assert integration.manifest["requirements"] == []
