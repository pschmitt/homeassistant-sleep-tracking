# Sleep Tracking

[![Open this integration in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=pschmitt&repository=homeassistant-sleep-tracking&category=integration)

Sleep Tracking uses a binary sensor that reports whether a person is in bed to
track sleep sessions. A configurable interruption threshold keeps brief
absences in the same session.

## Install

Use the badge above to add this repository as a custom integration in Home
Assistant Marketplace (Home Assistant 2026.11 or later), then install Sleep
Tracking. On older versions, add
`https://github.com/pschmitt/homeassistant-sleep-tracking` under
**HACS → Integrations → ⋮ → Custom repositories** with category
**Integration**. Neither route implies a public catalog listing.

## Setup

Add **Sleep Tracking** from **Settings → Devices & services → Add integration**.
For each person, enter a display name and select a binary sensor that is `on`
when they are in bed. The integration supports multiple people.

The options let you set the interruption threshold (default 30 minutes) and
minimum sleep duration (default 30 minutes). Sleep sessions shorter than the
minimum are not recorded as the last sleep duration.

## Entities

Each person gets an **In bed** binary sensor and sensors for **Bed start**,
**Last sleep duration**, **Last wake time**, and **Sleep interruptions**. Sleep
state is restored across Home Assistant restarts. If the selected sensor is
missing, reconfigure the integration to select its replacement.
