"""Coordinator for Peblar API data updates."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    PeblarApiAuthenticationError,
    PeblarApiClient,
    PeblarApiClientConnectionError,
    PeblarApiClientError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PeblarDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Manage fetching Peblar data from all relevant endpoints."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: PeblarApiClient,
    ) -> None:
        """Initialize Peblar data coordinator."""
        self.entry = entry
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch the latest data from the Peblar API."""
        try:
            system, evinterface, meter = await asyncio.gather(
                self.api.get_system(),
                self.api.get_evinterface(),
                self.api.get_meter(),
            )
        except PeblarApiAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except PeblarApiClientConnectionError as err:
            raise UpdateFailed("Unable to reach Peblar charger") from err
        except PeblarApiClientError as err:
            raise UpdateFailed(f"Peblar API error: {err}") from err

        return {
            "system": system,
            "evinterface": evinterface,
            "meter": meter,
        }
