"""Constants for the Peblar API integration."""

from homeassistant.const import Platform

DOMAIN = "peblar_api"
NAME = "Peblar API"

CONF_API_TOKEN = "api_token"
CONF_INTERVAL_EVINTERFACE_CHARGING = "interval_evinterface_charging"
CONF_INTERVAL_EVINTERFACE_IDLE = "interval_evinterface_idle"
CONF_INTERVAL_SYSTEM = "interval_system"
CONF_INTERVAL_METER_CHARGING = "interval_meter_charging"
CONF_INTERVAL_METER_IDLE = "interval_meter_idle"

SCAN_INTERVAL_BASE = 10          # evinterface polling interval (seconds)
SCAN_INTERVAL_EVINTERFACE_CHARGING = 10   # evinterface interval when charging
SCAN_INTERVAL_EVINTERFACE_IDLE = 30       # evinterface interval when idle
SCAN_INTERVAL_SYSTEM = 3600      # system endpoint polling interval (seconds)
SCAN_INTERVAL_METER_CHARGING = 10  # meter interval when charging (LockState=True)
SCAN_INTERVAL_METER_IDLE = 60    # meter interval when idle

DEFAULT_CURRENT_STEP_A = 0.05
MIN_CHARGE_CURRENT_A = 6.0
MAX_CHARGE_CURRENT_A = 20.0

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]
