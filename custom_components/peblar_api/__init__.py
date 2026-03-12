"""The Peblar API integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PeblarApiClient
from .const import (
    CONF_API_TOKEN,
    PLATFORMS,
)
from .coordinator import PeblarDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Peblar API integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Peblar API from a config entry."""

    client = PeblarApiClient(
        session=async_get_clientsession(hass),
        host=entry.data[CONF_HOST],
        api_token=entry.data[CONF_API_TOKEN],
    )
    coordinator = PeblarDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Peblar API config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
