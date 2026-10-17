"""Sensors for Sleep Tracking."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SleepTrackingEntity
from .tracker import SleepTracker


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sleep tracking sensors."""
    tracker: SleepTracker = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BedStartSensor(tracker),
            LastSleepDurationSensor(tracker),
            LastWakeTimeSensor(tracker),
            SleepInterruptionsSensor(tracker),
        ]
    )


class _SleepSensor(SleepTrackingEntity, SensorEntity):
    """Base class for sleep tracking sensors."""

    def __init__(self, tracker: SleepTracker, key: str) -> None:
        super().__init__(tracker)
        self._attr_unique_id = f"{tracker.config_entry.entry_id}_{key}"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.tracker.async_add_listener(self.async_write_ha_state))


class BedStartSensor(_SleepSensor):
    """Timestamp of when the current sleep session started."""

    _attr_translation_key = "bed_start"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:bed-clock"

    def __init__(self, tracker: SleepTracker) -> None:
        super().__init__(tracker, "bed_start")

    @property
    def native_value(self):
        return self.tracker.bed_start


class LastSleepDurationSensor(_SleepSensor):
    """Duration of the most recently completed sleep session, in hours."""

    _attr_translation_key = "last_sleep_duration"
    _attr_native_unit_of_measurement = "h"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:sleep"

    def __init__(self, tracker: SleepTracker) -> None:
        super().__init__(tracker, "last_sleep_duration")

    @property
    def native_value(self) -> float | None:
        return self.tracker.last_sleep_duration


class LastWakeTimeSensor(_SleepSensor):
    """Timestamp of the most recent wake-up."""

    _attr_translation_key = "last_wake_time"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:alarm"

    def __init__(self, tracker: SleepTracker) -> None:
        super().__init__(tracker, "last_wake_time")

    @property
    def native_value(self):
        return self.tracker.last_wake


class SleepInterruptionsSensor(_SleepSensor):
    """Number of brief interruptions during the current sleep session."""

    _attr_translation_key = "sleep_interruptions"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sleep-off"
    _attr_native_unit_of_measurement = None

    def __init__(self, tracker: SleepTracker) -> None:
        super().__init__(tracker, "sleep_interruptions")

    @property
    def native_value(self) -> int:
        return self.tracker.interruptions
