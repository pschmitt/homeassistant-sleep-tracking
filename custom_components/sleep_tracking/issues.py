"""Repair issue handling for the tracked in-bed sensor.

The tracked sensor belongs to another integration (a YAML template entity,
Withings, a pressure mat, ...) which may not have created its entities yet when
this integration sets up its config entry.  Checking once at setup time
therefore raises a bogus "sensor not found" repair on most restarts, and never
clears it again once the sensor does show up.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.start import async_at_started

from .const import CONF_IN_BED_SENSOR, DOMAIN, ISSUE_SENSOR_NOT_FOUND

_LOGGER = logging.getLogger(__name__)

# How long the sensor has to stay gone from the state machine before we raise
# the repair again — reloading its owning integration removes it briefly.
SENSOR_GONE_GRACE_PERIOD = timedelta(minutes=1)


@callback
def _async_issue_id(entry: ConfigEntry) -> str:
    """Return the repair issue id used for this config entry."""
    return f"{entry.entry_id}_{ISSUE_SENSOR_NOT_FOUND}"


@callback
def async_delete_sensor_issue(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clear the 'sensor not found' repair for this entry."""
    ir.async_delete_issue(hass, DOMAIN, _async_issue_id(entry))


@callback
def _async_check_sensor(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Raise or clear the repair depending on whether the sensor exists."""
    sensor_id = entry.data[CONF_IN_BED_SENSOR]

    if hass.states.get(sensor_id) is not None:
        async_delete_sensor_issue(hass, entry)
        return

    _LOGGER.warning(
        "Tracked in-bed sensor %s for '%s' does not exist", sensor_id, entry.title
    )
    ir.async_create_issue(
        hass,
        DOMAIN,
        _async_issue_id(entry),
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


@callback
def async_watch_sensor(hass: HomeAssistant, entry: ConfigEntry) -> CALLBACK_TYPE:
    """Keep the 'sensor not found' repair in sync with the tracked sensor.

    The first check is deferred until Home Assistant has finished starting, so a
    sensor that is merely late does not raise a repair.  Afterwards the repair is
    cleared as soon as the sensor reports a state again, and only re-raised once
    it has been gone for SENSOR_GONE_GRACE_PERIOD.

    Returns a callable that stops watching.
    """
    sensor_id = entry.data[CONF_IN_BED_SENSOR]
    cancel_recheck: CALLBACK_TYPE | None = None

    @callback
    def _async_cancel_recheck() -> None:
        nonlocal cancel_recheck
        if cancel_recheck is not None:
            cancel_recheck()
            cancel_recheck = None

    @callback
    def _async_recheck(_now) -> None:
        nonlocal cancel_recheck
        cancel_recheck = None
        _async_check_sensor(hass, entry)

    @callback
    def _async_sensor_changed(event: Event) -> None:
        nonlocal cancel_recheck

        if event.data.get("new_state") is None:
            # Gone from the state machine — give its integration a chance to
            # bring it back before complaining.
            if cancel_recheck is None:
                cancel_recheck = async_call_later(
                    hass, SENSOR_GONE_GRACE_PERIOD, _async_recheck
                )
            return

        # The sensor reported, so any outstanding repair is stale.
        _async_cancel_recheck()
        async_delete_sensor_issue(hass, entry)

    # Must be a @callback: async_at_started wraps this in a HassJob, and an
    # undecorated function would be run in an executor thread.
    @callback
    def _async_initial_check(_hass: HomeAssistant) -> None:
        _async_check_sensor(hass, entry)

    unsub_state = async_track_state_change_event(
        hass, [sensor_id], _async_sensor_changed
    )
    cancel_started = async_at_started(hass, _async_initial_check)

    @callback
    def _async_stop() -> None:
        _async_cancel_recheck()
        cancel_started()
        unsub_state()

    return _async_stop
