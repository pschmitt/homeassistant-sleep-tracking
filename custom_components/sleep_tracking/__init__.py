"""The Sleep Tracking integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .issues import async_delete_sensor_issue, async_watch_sensor
from .tracker import SleepTracker


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sleep Tracking from a config entry."""
    tracker = SleepTracker(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = tracker

    # Set up platforms first — entities call async_added_to_hass and restore
    # the tracker's state before we start listening to state changes.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await tracker.async_start()

    # Raise/clear the "sensor not found" repair as the tracked sensor comes and
    # goes.  The first check waits for HA to finish starting, because the sensor
    # usually belongs to an integration that sets up after this one.
    entry.async_on_unload(async_watch_sensor(hass, entry))

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

    async_delete_sensor_issue(hass, entry)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
