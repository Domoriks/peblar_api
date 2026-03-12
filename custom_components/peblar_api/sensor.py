"""Sensor platform for Peblar API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PeblarDataUpdateCoordinator


def _ma_to_a(v: Any) -> float | None:
    """Convert milliamps to amps."""
    if v is None:
        return None
    try:
        return float(v) / 1000
    except (TypeError, ValueError):
        return None


def _list_to_str(v: Any) -> str | None:
    """Convert a list of codes to a comma-separated string, or 'None'."""
    if v is None:
        return None
    if isinstance(v, list):
        return ", ".join(str(c) for c in v) if v else "None"
    return str(v)


_CP_STATE_MAP: dict[str, str] = {
    "STATE A": "No vehicle connected",
    "STATE B": "Vehicle connected, not charging",
    "STATE C": "Charging",
    "STATE D": "Charging with ventilation",
    "STATE E": "Error",
    "STATE F": "Not available",
}


def _cp_state_to_str(v: Any) -> str | None:
    """Map CP state string to a human-readable string."""
    if v is None:
        return None
    return _CP_STATE_MAP.get(str(v).upper(), str(v))


@dataclass(frozen=True, kw_only=True)
class PeblarSensorEntityDescription(SensorEntityDescription):
    """Extend SensorEntityDescription with endpoint and optional converter."""

    endpoint: str = ""
    value_fn: Callable[[Any], StateType] | None = None


SENSOR_DEFINITIONS: tuple[PeblarSensorEntityDescription, ...] = (
    # ── System ──────────────────────────────────────────────────────────────
    PeblarSensorEntityDescription(
        key="FirmwareVersion",
        endpoint="system",
        name="Firmware Version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="ProductSn",
        endpoint="system",
        name="Serial Number",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="ProductPn",
        endpoint="system",
        name="Product Part Number",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="PhaseCount",
        endpoint="system",
        name="Phase Count",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="Uptime",
        endpoint="system",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="CellularSignalStrength",
        endpoint="system",
        name="Cellular Signal Strength",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="WlanSignalStrength",
        endpoint="system",
        name="WLAN Signal Strength",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="ActiveErrorCodes",
        endpoint="system",
        name="Active Error Codes",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_list_to_str,
    ),
    PeblarSensorEntityDescription(
        key="ActiveWarningCodes",
        endpoint="system",
        name="Active Warning Codes",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_list_to_str,
    ),
    # ── Meter ────────────────────────────────────────────────────────────────
    PeblarSensorEntityDescription(
        key="CurrentPhase1",
        endpoint="meter",
        name="Current Phase 1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_ma_to_a,
    ),
    PeblarSensorEntityDescription(
        key="CurrentPhase2",
        endpoint="meter",
        name="Current Phase 2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_ma_to_a,
    ),
    PeblarSensorEntityDescription(
        key="CurrentPhase3",
        endpoint="meter",
        name="Current Phase 3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_ma_to_a,
    ),
    PeblarSensorEntityDescription(
        key="EnergySession",
        endpoint="meter",
        name="Energy Session",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    PeblarSensorEntityDescription(
        key="EnergyTotal",
        endpoint="meter",
        name="Energy Total",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    PeblarSensorEntityDescription(
        key="PowerPhase1",
        endpoint="meter",
        name="Power Phase 1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PeblarSensorEntityDescription(
        key="PowerPhase2",
        endpoint="meter",
        name="Power Phase 2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PeblarSensorEntityDescription(
        key="PowerPhase3",
        endpoint="meter",
        name="Power Phase 3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PeblarSensorEntityDescription(
        key="PowerTotal",
        endpoint="meter",
        name="Power Total",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PeblarSensorEntityDescription(
        key="VoltagePhase1",
        endpoint="meter",
        name="Voltage Phase 1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PeblarSensorEntityDescription(
        key="VoltagePhase2",
        endpoint="meter",
        name="Voltage Phase 2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PeblarSensorEntityDescription(
        key="VoltagePhase3",
        endpoint="meter",
        name="Voltage Phase 3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── EV Interface ─────────────────────────────────────────────────────────
    PeblarSensorEntityDescription(
        key="ChargeCurrentLimit",
        endpoint="evinterface",
        name="Charge Current Limit",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_ma_to_a,
    ),
    PeblarSensorEntityDescription(
        key="ChargeCurrentLimitActual",
        endpoint="evinterface",
        name="Charge Current Limit Actual",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_ma_to_a,
    ),
    PeblarSensorEntityDescription(
        key="ChargeCurrentLimitSource",
        endpoint="evinterface",
        name="Charge Current Limit Source",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="CpState",
        endpoint="evinterface",
        name="Charge State",
        icon="mdi:ev-station",
        value_fn=_cp_state_to_str,
    ),
    PeblarSensorEntityDescription(
        key="Force1Phase",
        endpoint="evinterface",
        name="Force Single Phase",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PeblarSensorEntityDescription(
        key="LockState",
        endpoint="evinterface",
        name="Lock State",
        icon="mdi:lock",
    ),
)


class PeblarSensor(CoordinatorEntity[PeblarDataUpdateCoordinator], SensorEntity):
    """Representation of a Peblar sensor."""

    _attr_has_entity_name = True
    entity_description: PeblarSensorEntityDescription

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: PeblarDataUpdateCoordinator,
        description: PeblarSensorEntityDescription,
    ) -> None:
        """Initialize Peblar sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> StateType:
        """Return the current sensor value."""
        payload = self.coordinator.data.get(self.entity_description.endpoint, {})
        if not isinstance(payload, dict):
            return None
        raw = payload.get(self.entity_description.key)
        if self.entity_description.value_fn is not None:
            return self.entity_description.value_fn(raw)
        return raw  # type: ignore[return-value]

    @property
    def device_info(self) -> DeviceInfo:
        """Return metadata for the Peblar charger device."""
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
    """Set up Peblar sensors based on a config entry."""
    coordinator: PeblarDataUpdateCoordinator = entry.runtime_data

    async_add_entities(
        PeblarSensor(entry, coordinator, description)
        for description in SENSOR_DEFINITIONS
    )
