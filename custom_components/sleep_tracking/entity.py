"""Base entity class for Sleep Tracking."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import CONF_PERSON_NAME, DOMAIN
from .tracker import SleepTracker


class SleepTrackingEntity(Entity):
    """Base class for all sleep tracking entities."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, tracker: SleepTracker) -> None:
        self.tracker = tracker

    @property
    def device_info(self) -> DeviceInfo:
        entry = self.tracker.config_entry
        person = entry.data.get(CONF_PERSON_NAME, entry.title)
        return DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"{person} Sleep Tracker",
            manufacturer="Sleep Tracking",
            model="Sleep Tracker",
            entry_type=DeviceEntryType.SERVICE,
        )
