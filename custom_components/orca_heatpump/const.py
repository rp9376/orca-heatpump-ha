"""Constants for the Orca Heat Pump integration."""

from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "orca_heatpump"
LOGGER = logging.getLogger(__package__)

SCAN_INTERVAL: Final = timedelta(seconds=30)
# Timer programmes only change on the display; 165 tags aren't worth 30 s.
TIMER_SCAN_INTERVAL: Final = timedelta(hours=1)

UNKNOWN_ALARM: Final = "unknown_code"
DEFAULT_USERNAME: Final = "admin"
DEFAULT_TITLE: Final = "Orca heat pump"

CONF_TOPOLOGY: Final = "topology"
CONF_ALLOW_POWER_LIMITS: Final = "allow_power_limits"

# orca-energy-ha, which must not poll the same pump (ADR 0001).
OLD_DOMAIN: Final = "orca"
OLD_CONF_HOST: Final = "hostname"

# Consecutive polls refused with E_TOO_MANY_USERS before a repair issue.
SESSIONS_EXHAUSTED_AFTER: Final = 3
