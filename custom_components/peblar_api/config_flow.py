"""Config flow for Peblar API."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    PeblarApiAuthenticationError,
    PeblarApiClient,
    PeblarApiClientConnectionError,
    PeblarApiClientError,
)
from .const import (
    CONF_API_TOKEN,
    CONF_INTERVAL_EVINTERFACE_CHARGING,
    CONF_INTERVAL_EVINTERFACE_IDLE,
    CONF_INTERVAL_METER_CHARGING,
    CONF_INTERVAL_METER_IDLE,
    CONF_INTERVAL_SYSTEM,
    DOMAIN,
    SCAN_INTERVAL_EVINTERFACE_CHARGING,
    SCAN_INTERVAL_EVINTERFACE_IDLE,
    SCAN_INTERVAL_METER_CHARGING,
    SCAN_INTERVAL_METER_IDLE,
    SCAN_INTERVAL_SYSTEM,
)

_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_API_TOKEN): str,
    }
)


def _normalize_host(host: str) -> str:
    """Normalize user-provided host input."""
    normalized = host.strip().removeprefix("http://").removeprefix("https://")
    normalized = normalized.split("/", maxsplit=1)[0]
    return normalized.strip()


class PeblarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Peblar API."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> PeblarOptionsFlow:
        """Return the options flow handler."""
        return PeblarOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = _normalize_host(user_input[CONF_HOST])
            api_token = user_input[CONF_API_TOKEN].strip()

            if not host or not api_token:
                errors["base"] = "invalid_input"
            else:
                client = PeblarApiClient(
                    session=async_get_clientsession(self.hass),
                    host=host,
                    api_token=api_token,
                )

                try:
                    system = await client.get_system()
                except PeblarApiAuthenticationError:
                    errors["base"] = "invalid_auth"
                except PeblarApiClientConnectionError:
                    errors["base"] = "cannot_connect"
                except PeblarApiClientError:
                    errors["base"] = "unknown"
                else:
                    serial = (system or {}).get("ProductSn") or host.lower()
                    await self.async_set_unique_id(str(serial).lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Peblar API",
                        data={
                            CONF_HOST: host,
                            CONF_API_TOKEN: api_token,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_USER_SCHEMA,
            errors=errors,
        )


class PeblarOptionsFlow(config_entries.OptionsFlow):
    """Handle Peblar API options."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERVAL_EVINTERFACE_CHARGING,
                        default=opts.get(CONF_INTERVAL_EVINTERFACE_CHARGING, SCAN_INTERVAL_EVINTERFACE_CHARGING),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    vol.Required(
                        CONF_INTERVAL_EVINTERFACE_IDLE,
                        default=opts.get(CONF_INTERVAL_EVINTERFACE_IDLE, SCAN_INTERVAL_EVINTERFACE_IDLE),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    vol.Required(
                        CONF_INTERVAL_SYSTEM,
                        default=opts.get(CONF_INTERVAL_SYSTEM, SCAN_INTERVAL_SYSTEM),
                    ): vol.All(vol.Coerce(int), vol.Range(min=60)),
                    vol.Required(
                        CONF_INTERVAL_METER_CHARGING,
                        default=opts.get(CONF_INTERVAL_METER_CHARGING, SCAN_INTERVAL_METER_CHARGING),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    vol.Required(
                        CONF_INTERVAL_METER_IDLE,
                        default=opts.get(CONF_INTERVAL_METER_IDLE, SCAN_INTERVAL_METER_IDLE),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                }
            ),
        )
