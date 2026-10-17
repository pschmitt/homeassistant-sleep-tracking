"""Sleep tracking state machine."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    CONF_IN_BED_SENSOR,
    CONF_INTERRUPTION_THRESHOLD,
    CONF_MIN_SLEEP_DURATION,
    DEFAULT_INTERRUPTION_THRESHOLD,
    DEFAULT_MIN_SLEEP_DURATION,
)

_LOGGER = logging.getLogger(__name__)


class SleepTracker:
    """Event-driven state machine that tracks sleep sessions.

    Distinguishes brief interruptions (bathroom trips, tossing) from genuine
    wake-ups using a configurable threshold.  Brief absences preserve the
    original bed_start so the final duration reflects the full sleep window.
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry

        self.in_bed: bool | None = None
        self.bed_start: datetime | None = None
        self.out_of_bed_since: datetime | None = None
        self.last_wake: datetime | None = None
        self.last_sleep_duration: float | None = None
        self.interruptions: int = 0

        self._listeners: list[Callable[[], None]] = []
        self._unsubscribe: Callable[[], None] | None = None

    # ------------------------------------------------------------------
    # Properties derived from config options
    # ------------------------------------------------------------------

    @property
    def interruption_threshold(self) -> timedelta:
        minutes = self.config_entry.options.get(
            CONF_INTERRUPTION_THRESHOLD, DEFAULT_INTERRUPTION_THRESHOLD
        )
        return timedelta(minutes=float(minutes))

    @property
    def min_sleep_duration(self) -> timedelta:
        minutes = self.config_entry.options.get(CONF_MIN_SLEEP_DURATION, DEFAULT_MIN_SLEEP_DURATION)
        return timedelta(minutes=float(minutes))

    # ------------------------------------------------------------------
    # Listener management (entities subscribe here)
    # ------------------------------------------------------------------

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Subscribe to tracker state changes; returns an unsubscribe callable."""
        self._listeners.append(listener)

        @callback
        def _remove() -> None:
            self._listeners.remove(listener)

        return _remove

    @callback
    def _async_notify(self) -> None:
        for listener in self._listeners:
            listener()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Begin watching the configured in-bed binary sensor."""
        sensor_id = self.config_entry.data[CONF_IN_BED_SENSOR]

        # Seed the initial in-bed state from the current sensor state so we
        # don't miss the session that started before this integration was set up.
        current = self.hass.states.get(sensor_id)
        if current is not None and current.state == "on" and self.in_bed is not True:
            if self.bed_start is None:
                self.bed_start = dt_util.utcnow()
            self.in_bed = True
            self.out_of_bed_since = None
            self._async_notify()
        elif current is not None and current.state == "off" and self.in_bed is None:
            self.in_bed = False
            if self.out_of_bed_since is None:
                self.out_of_bed_since = dt_util.utcnow()
            self._async_notify()

        self._unsubscribe = async_track_state_change_event(
            self.hass, [sensor_id], self._async_state_changed
        )
        _LOGGER.debug(
            "Sleep tracker for '%s' started, watching %s (current state: %s)",
            self.config_entry.title,
            sensor_id,
            current.state if current else "unavailable",
        )

    @callback
    def async_stop(self) -> None:
        """Stop watching state changes."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    # ------------------------------------------------------------------
    # State change handler
    # ------------------------------------------------------------------

    @callback
    def _async_state_changed(self, event: Event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        if new_state.state == "on":
            self._async_handle_in_bed()
            self._async_notify()
        elif new_state.state == "off":
            self._async_handle_out_of_bed()
            self._async_notify()
        # Silently ignore unavailable / unknown — don't reset tracker state.

    @callback
    def _async_handle_in_bed(self) -> None:
        if self.in_bed is True:
            return

        now = dt_util.utcnow()

        if self.out_of_bed_since is None or self.bed_start is None:
            # First ever session (or a very long absence with no recorded end).
            self.bed_start = now
            self.interruptions = 0
        else:
            absence = now - self.out_of_bed_since
            if absence > self.interruption_threshold:
                _LOGGER.debug(
                    "New sleep session (absence %s > threshold %s)",
                    absence,
                    self.interruption_threshold,
                )
                self.bed_start = now
                self.interruptions = 0
            else:
                self.interruptions += 1
                _LOGGER.debug(
                    "Brief interruption #%d (absence %s)",
                    self.interruptions,
                    absence,
                )

        self.out_of_bed_since = None
        self.in_bed = True

    @callback
    def _async_handle_out_of_bed(self) -> None:
        if self.in_bed is False:
            return

        now = dt_util.utcnow()
        self.out_of_bed_since = now
        self.in_bed = False

        if self.bed_start is not None:
            elapsed = now - self.bed_start
            if elapsed >= self.min_sleep_duration:
                hours = elapsed.total_seconds() / 3600
                self.last_sleep_duration = round(hours, 2)
                self.last_wake = now
                _LOGGER.debug(
                    "Sleep ended: %.2f h (bed_start=%s, interruptions=%d)",
                    hours,
                    self.bed_start,
                    self.interruptions,
                )

    # ------------------------------------------------------------------
    # State restoration (called by the binary sensor on HA restart)
    # ------------------------------------------------------------------

    def restore_state(
        self,
        *,
        in_bed: bool | None,
        bed_start: datetime | None,
        out_of_bed_since: datetime | None,
        last_wake: datetime | None,
        last_sleep_duration: float | None,
        interruptions: int,
    ) -> None:
        self.in_bed = in_bed
        self.bed_start = bed_start
        self.out_of_bed_since = out_of_bed_since
        self.last_wake = last_wake
        self.last_sleep_duration = last_sleep_duration
        self.interruptions = interruptions
        _LOGGER.debug(
            "Restored: in_bed=%s bed_start=%s interruptions=%d",
            in_bed,
            bed_start,
            interruptions,
        )
