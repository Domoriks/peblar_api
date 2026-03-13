"""Coordinator for Peblar API data updates."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    PeblarApiAuthenticationError,
    PeblarApiClient,
    PeblarApiClientConnectionError,
    PeblarApiClientError,
)
from .const import (
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
        self._last_system_update: datetime | None = None
        self._last_meter_update: datetime | None = None
        self._last_evinterface_update: datetime | None = None

        # Use the charging interval as the base tick; idle is always longer
        evinterface_interval = min(
            entry.options.get(CONF_INTERVAL_EVINTERFACE_CHARGING, SCAN_INTERVAL_EVINTERFACE_CHARGING),
            entry.options.get(CONF_INTERVAL_EVINTERFACE_IDLE, SCAN_INTERVAL_EVINTERFACE_IDLE),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=evinterface_interval),
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch the latest data from the Peblar API."""
        now = dt_util.utcnow()

        last_evinterface = (self.data or {}).get("evinterface", {})
        charging = bool(last_evinterface.get("LockState", False))

        evinterface_interval = (
            self.entry.options.get(CONF_INTERVAL_EVINTERFACE_CHARGING, SCAN_INTERVAL_EVINTERFACE_CHARGING)
            if charging
            else self.entry.options.get(CONF_INTERVAL_EVINTERFACE_IDLE, SCAN_INTERVAL_EVINTERFACE_IDLE)
        )
        fetch_evinterface = (
            self._last_evinterface_update is None
            or (now - self._last_evinterface_update).total_seconds() >= evinterface_interval
        )

        fetch_system = (
            self._last_system_update is None
            or (now - self._last_system_update).total_seconds() >= self.entry.options.get(CONF_INTERVAL_SYSTEM, SCAN_INTERVAL_SYSTEM)
        )

        meter_interval = (
            self.entry.options.get(CONF_INTERVAL_METER_CHARGING, SCAN_INTERVAL_METER_CHARGING)
            if charging
            else self.entry.options.get(CONF_INTERVAL_METER_IDLE, SCAN_INTERVAL_METER_IDLE)
        )
        fetch_meter = (
            self._last_meter_update is None
            or (now - self._last_meter_update).total_seconds() >= meter_interval
        )

        _LOGGER.debug(
            "Update cycle | charging=%s | fetch evinterface=%s system=%s meter=%s",
            charging,
            fetch_evinterface,
            fetch_system,
            fetch_meter,
        )

        coros: list = []
        if fetch_evinterface:
            coros.append(self.api.get_evinterface())
        if fetch_system:
            coros.append(self.api.get_system())
        if fetch_meter:
            coros.append(self.api.get_meter())

        try:
            results = await asyncio.gather(*coros)
        except PeblarApiAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except PeblarApiClientConnectionError as err:
            raise UpdateFailed("Unable to reach Peblar charger") from err
        except PeblarApiClientError as err:
            raise UpdateFailed(f"Peblar API error: {err}") from err

        idx = 0

        if fetch_evinterface:
            evinterface = results[idx]; idx += 1
            self._last_evinterface_update = now
        else:
            evinterface = (self.data or {}).get("evinterface", {})

        if fetch_system:
            system = results[idx]; idx += 1
            self._last_system_update = now
        else:
            system = (self.data or {}).get("system", {})

        if fetch_meter:
            meter = results[idx]
            self._last_meter_update = now
        else:
            meter = (self.data or {}).get("meter", {})

        return {
            "system": system,
            "evinterface": evinterface,
            "meter": meter,
        }
