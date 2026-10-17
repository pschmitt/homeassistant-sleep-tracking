"""Binary sensor for Sleep Tracking: is the person currently in bed?

This entity also acts as the persistence layer: it stores all tracker state
as extra_state_attributes so it can be restored across HA restarts via
RestoreEntity.
"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_BED_START,
    ATTR_INTERRUPTIONS,
    ATTR_LAST_SLEEP_DURATION,
    ATTR_LAST_WAKE,
    ATTR_OUT_OF_BED_SINCE,
    DOMAIN,
)
from .entity import SleepTrackingEntity
from .tracker import SleepTracker


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the in-bed binary sensor."""
    tracker: SleepTracker = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([InBedBinarySensor(tracker)])


class InBedBinarySensor(SleepTrackingEntity, RestoreEntity, BinarySensorEntity):
    """Binary sensor that reflects the current in-bed state.

    Stores full tracker state as attributes so that a restart can resume
    without losing the current sleep session.
    """

    _attr_translation_key = "in_bed"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, tracker: SleepTracker) -> None:
        super().__init__(tracker)
        self._attr_unique_id = f"{tracker.config_entry.entry_id}_in_bed"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._async_restore_tracker_state()
        self.async_on_remove(self.tracker.async_add_listener(self.async_write_ha_state))

    async def _async_restore_tracker_state(self) -> None:
        last_state = await self.async_get_last_state()
        if last_state is None or last_state.state not in ("on", "off"):
            return

        attrs = last_state.attributes

        def _parse_dt(key: str):
            val = attrs.get(key)
            return dt_util.parse_datetime(val) if val else None

        raw_duration = attrs.get(ATTR_LAST_SLEEP_DURATION)

        self.tracker.restore_state(
            in_bed=last_state.state == "on",
            bed_start=_parse_dt(ATTR_BED_START),
            out_of_bed_since=_parse_dt(ATTR_OUT_OF_BED_SINCE),
            last_wake=_parse_dt(ATTR_LAST_WAKE),
            last_sleep_duration=float(raw_duration) if raw_duration is not None else None,
            interruptions=int(attrs.get(ATTR_INTERRUPTIONS, 0)),
        )

    @property
    def is_on(self) -> bool | None:
        return self.tracker.in_bed

    @property
    def extra_state_attributes(self) -> dict:
        """Persist all tracker state so it can be restored on restart."""
        attrs: dict = {ATTR_INTERRUPTIONS: self.tracker.interruptions}
        if self.tracker.bed_start is not None:
            attrs[ATTR_BED_START] = self.tracker.bed_start.isoformat()
        if self.tracker.out_of_bed_since is not None:
            attrs[ATTR_OUT_OF_BED_SINCE] = self.tracker.out_of_bed_since.isoformat()
        if self.tracker.last_wake is not None:
            attrs[ATTR_LAST_WAKE] = self.tracker.last_wake.isoformat()
        if self.tracker.last_sleep_duration is not None:
            attrs[ATTR_LAST_SLEEP_DURATION] = self.tracker.last_sleep_duration
        return attrs
