"""Config flow for the Orca Heat Pump integration."""

from collections.abc import Mapping
from typing import Any, override

import probatio

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .client.client import OrcaClient
from .client.errors import (
    OrcaAuthError,
    OrcaConnectionError,
    OrcaError,
    OrcaTooManyUsersError,
)
from .client.models import PumpTopology
from .const import (
    CONF_ALLOW_POWER_LIMITS,
    CONF_BUFFER,
    CONF_ROOM_SENSORS,
    CONF_SOLAR,
    CONF_TOPOLOGY,
    DEFAULT_TITLE,
    DEFAULT_USERNAME,
    DOMAIN,
    LOGGER,
    OLD_CONF_HOST,
    OLD_DOMAIN,
    OVERRIDE_ABSENT,
    OVERRIDE_AUTO,
    OVERRIDE_PRESENT,
)
from .helpers import split_host, topology_from_data, topology_to_data

PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
CONNECTION_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_HOST): TextSelector(),
        probatio.Required(CONF_USERNAME, default=DEFAULT_USERNAME): TextSelector(),
        probatio.Required(CONF_PASSWORD): PASSWORD,
    }
)
USER_SCHEMA = CONNECTION_SCHEMA.extend(
    {probatio.Required(CONF_ALLOW_POWER_LIMITS, default=False): BooleanSelector()}
)
OVERRIDE = SelectSelector(
    SelectSelectorConfig(
        options=[OVERRIDE_AUTO, OVERRIDE_PRESENT, OVERRIDE_ABSENT],
        mode=SelectSelectorMode.DROPDOWN,
        translation_key="override",
    )
)


async def validate(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> tuple[dict[str, str], PumpTopology | None]:
    """Connect, read the topology and log out; return errors or the topology."""
    host, port = split_host(data[CONF_HOST])
    client = OrcaClient(
        async_get_clientsession(hass),
        host,
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
        port=port,
    )
    try:
        topology = await client.async_detect_topology()
    except OrcaAuthError:
        return {"base": "invalid_auth"}, None
    except OrcaTooManyUsersError:
        return {"base": "too_many_users"}, None
    except OrcaConnectionError:
        return {"base": "cannot_connect"}, None
    except OrcaError:
        return {"base": "not_orca"}, None
    except Exception:  # noqa: BLE001
        LOGGER.exception("Unexpected error while connecting to %s", host)
        return {"base": "unknown"}, None
    finally:
        await client.async_logout()
    return {}, topology


def old_integration_has(hass: HomeAssistant, host: str) -> bool:
    """Return whether orca-energy-ha is set up for this host."""
    host = split_host(host)[0]
    return any(
        host in (entry.unique_id, entry.data.get(OLD_CONF_HOST))
        for entry in hass.config_entries.async_entries(OLD_DOMAIN)
    )


class OrcaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up an Orca heat pump."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._data: dict[str, Any] = {}
        self._options: dict[str, Any] = {}

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OrcaOptionsFlow:
        """Return the options flow."""
        return OrcaOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the display's address and login."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()
            data = {
                CONF_HOST: host,
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            errors, topology = await validate(self.hass, data)
            if topology is not None:
                self._data = data | {CONF_TOPOLOGY: topology_to_data(topology)}
                self._options = {
                    CONF_ALLOW_POWER_LIMITS: user_input[CONF_ALLOW_POWER_LIMITS]
                }
                if old_integration_has(self.hass, host):
                    return await self.async_step_old_integration()
                return self._create_entry()
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_old_integration(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Warn that orca-energy-ha polls the same pump."""
        if user_input is not None:
            return self._create_entry()
        return self.async_show_form(
            step_id="old_integration",
            description_placeholders={"host": self._data[CONF_HOST]},
        )

    def _create_entry(self) -> ConfigFlowResult:
        return self.async_create_entry(
            title=DEFAULT_TITLE, data=self._data, options=self._options
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication after the display refused the login."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the login again."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors, topology = await validate(self.hass, entry.data | user_input)
            if topology is not None:
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )
        schema = probatio.Schema(
            {
                probatio.Required(CONF_USERNAME): TextSelector(),
                probatio.Required(CONF_PASSWORD): PASSWORD,
            }
        )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or {CONF_USERNAME: entry.data[CONF_USERNAME]}
            ),
            description_placeholders={"host": entry.data[CONF_HOST]},
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the address or login."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            if host.lower() != entry.unique_id:
                await self.async_set_unique_id(host.lower())
                self._abort_if_unique_id_configured()
            data = user_input | {CONF_HOST: host}
            errors, topology = await validate(self.hass, data)
            if topology is not None:
                return self.async_update_reload_and_abort(
                    entry, unique_id=host.lower(), data_updates=data
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                CONNECTION_SCHEMA,
                user_input
                or {
                    CONF_HOST: entry.data[CONF_HOST],
                    CONF_USERNAME: entry.data[CONF_USERNAME],
                },
            ),
            errors=errors,
        )


class OrcaOptionsFlow(OptionsFlowWithReload):
    """Power limit permission and corrections for topology detection."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        topology = topology_from_data(self.config_entry.data[CONF_TOPOLOGY])
        fields: dict[Any, Any] = {
            probatio.Required(CONF_ALLOW_POWER_LIMITS, default=False): BooleanSelector()
        }
        for circuit in topology.circuits:
            fields[
                probatio.Required(
                    CONF_ROOM_SENSORS[circuit.slot - 1], default=OVERRIDE_AUTO
                )
            ] = OVERRIDE
        fields[probatio.Required(CONF_SOLAR, default=OVERRIDE_AUTO)] = OVERRIDE
        fields[probatio.Required(CONF_BUFFER, default=OVERRIDE_AUTO)] = OVERRIDE
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                probatio.Schema(fields), self.config_entry.options
            ),
        )
