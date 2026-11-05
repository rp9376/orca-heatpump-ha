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
CONF_SOLAR: Final = "solar"
CONF_BUFFER: Final = "buffer"
CONF_ROOM_SENSORS: Final = ("room_sensor_1", "room_sensor_2", "room_sensor_3")

OVERRIDE_AUTO: Final = "auto"
OVERRIDE_PRESENT: Final = "present"
OVERRIDE_ABSENT: Final = "absent"

# orca-energy-ha, which must not poll the same pump (ADR 0001).
OLD_DOMAIN: Final = "orca"
OLD_CONF_HOST: Final = "hostname"

# Consecutive polls refused with E_TOO_MANY_USERS before a repair issue.
SESSIONS_EXHAUSTED_AFTER: Final = 3
