"""The Sleep Tracking integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_IN_BED_SENSOR,
    DOMAIN,
    ISSUE_SENSOR_NOT_FOUND,
    PLATFORMS,
)
from .tracker import SleepTracker


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sleep Tracking from a config entry."""
    tracker = SleepTracker(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = tracker

    # Set up platforms first — entities call async_added_to_hass and restore
    # the tracker's state before we start listening to state changes.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await tracker.async_start()

    # Raise a repair if the tracked entity is not known to HA yet.
    _async_check_sensor(hass, entry)

    entry.async_on_unload(
        entry.add_update_listener(
            lambda _hass, _entry: _entry.async_schedule_reload()
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Sleep Tracking config entry."""
    tracker: SleepTracker = hass.data[DOMAIN][entry.entry_id]
    tracker.async_stop()

    ir.async_delete_issue(hass, DOMAIN, f"{entry.entry_id}_{ISSUE_SENSOR_NOT_FOUND}")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _async_check_sensor(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create or clear a repair issue based on whether the sensor exists."""
    sensor_id = entry.data[CONF_IN_BED_SENSOR]
    issue_id = f"{entry.entry_id}_{ISSUE_SENSOR_NOT_FOUND}"

    if hass.states.get(sensor_id) is None:
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            is_persistent=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_SENSOR_NOT_FOUND,
            translation_placeholders={
                "entity_id": sensor_id,
                "name": entry.title,
            },
            data={"entry_id": entry.entry_id},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, issue_id)


