"""Constants for the Sleep Tracking integration."""

from homeassistant.const import Platform

DOMAIN = "sleep_tracking"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

# Config entry data (require reconfigure to change)
CONF_PERSON_NAME = "person_name"
CONF_IN_BED_SENSOR = "in_bed_sensor"

# Config entry options (changeable via options flow, trigger reload)
CONF_INTERRUPTION_THRESHOLD = "interruption_threshold"
CONF_MIN_SLEEP_DURATION = "min_sleep_duration"

# Defaults
DEFAULT_INTERRUPTION_THRESHOLD = 30  # minutes
DEFAULT_MIN_SLEEP_DURATION = 30  # minutes
MIN_INTERRUPTION_THRESHOLD = 1
MAX_INTERRUPTION_THRESHOLD = 240
MIN_SLEEP_DURATION = 5
MAX_SLEEP_DURATION = 120

# Issue IDs (prefixed with entry_id at runtime)
ISSUE_SENSOR_NOT_FOUND = "sensor_not_found"

# Attribute keys stored in the binary sensor for state restoration
ATTR_BED_START = "bed_start"
ATTR_OUT_OF_BED_SINCE = "out_of_bed_since"
ATTR_LAST_WAKE = "last_wake"
ATTR_LAST_SLEEP_DURATION = "last_sleep_duration"
ATTR_INTERRUPTIONS = "interruptions"
