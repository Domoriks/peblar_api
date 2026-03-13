"""Number platform for Peblar API charger controls."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_CURRENT_STEP_A, DOMAIN, MAX_CHARGE_CURRENT_A
from .coordinator import PeblarDataUpdateCoordinator


class PeblarChargeCurrentLimit(CoordinatorEntity[PeblarDataUpdateCoordinator], NumberEntity):
    """Charge current limit control (maps ChargeCurrentLimit mA <-> A)."""

    _attr_has_entity_name = True
    _attr_name = "Charge Current Limit"
    _attr_unique_id_suffix = "charge_current_limit"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_min_value = 0.0
    _attr_native_max_value = MAX_CHARGE_CURRENT_A
    _attr_native_step = DEFAULT_CURRENT_STEP_A
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: PeblarDataUpdateCoordinator,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_charge_current_limit"

    @property
    def native_value(self) -> float | None:
        """Return current charge current limit in amps."""
        ev = self.coordinator.data.get("evinterface", {})
        val = ev.get("ChargeCurrentLimit")
        if val is None:
            return None
        try:
            return float(val) / 1000
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the charge current limit (converts A to mA for the API)."""
        updated = await self.coordinator.api.patch_evinterface({"ChargeCurrentLimit": int(value * 1000)})
        if isinstance(updated, dict) and updated:
            self.coordinator.data["evinterface"].update(updated)
            self.coordinator.async_set_updated_data(self.coordinator.data)
        else:
            await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata."""
        system = self.coordinator.data.get("system", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer="Peblar",
            model=system.get("ProductPn"),
            serial_number=system.get("ProductSn"),
            sw_version=system.get("FirmwareVersion"),
            configuration_url=f"http://{self._entry.data[CONF_HOST]}",
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Peblar number entities based on a config entry."""
    coordinator: PeblarDataUpdateCoordinator = entry.runtime_data
    async_add_entities([PeblarChargeCurrentLimit(entry, coordinator)])
