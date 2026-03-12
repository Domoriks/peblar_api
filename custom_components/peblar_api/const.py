"""Constants for the Peblar API integration."""

from homeassistant.const import Platform

DOMAIN = "peblar_api"
NAME = "Peblar API"

CONF_API_TOKEN = "api_token"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 3
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 60
DEFAULT_CURRENT_STEP_A = 0.05
MIN_CHARGE_CURRENT_A = 6.0
MAX_CHARGE_CURRENT_A = 20.0

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]
