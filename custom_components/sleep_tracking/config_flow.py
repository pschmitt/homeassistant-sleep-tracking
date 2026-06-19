"""Config flow for the Sleep Tracking integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_IN_BED_SENSOR,
    CONF_INTERRUPTION_THRESHOLD,
    CONF_MIN_SLEEP_DURATION,
    CONF_PERSON_NAME,
    DEFAULT_INTERRUPTION_THRESHOLD,
    DEFAULT_MIN_SLEEP_DURATION,
    DOMAIN,
    MAX_INTERRUPTION_THRESHOLD,
    MAX_SLEEP_DURATION,
    MIN_INTERRUPTION_THRESHOLD,
    MIN_SLEEP_DURATION,
)


def _data_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_PERSON_NAME,
                default=d.get(CONF_PERSON_NAME, ""),
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
            vol.Required(
                CONF_IN_BED_SENSOR,
                default=d.get(CONF_IN_BED_SENSOR),
            ): EntitySelector(
                EntitySelectorConfig(domain="binary_sensor"),
            ),
        }
    )


def _options_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_INTERRUPTION_THRESHOLD,
                default=options.get(
                    CONF_INTERRUPTION_THRESHOLD, DEFAULT_INTERRUPTION_THRESHOLD
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_INTERRUPTION_THRESHOLD,
                    max=MAX_INTERRUPTION_THRESHOLD,
                    step=5,
                    mode=NumberSelectorMode.SLIDER,
                    unit_of_measurement="min",
                )
            ),
            vol.Required(
                CONF_MIN_SLEEP_DURATION,
                default=options.get(
                    CONF_MIN_SLEEP_DURATION, DEFAULT_MIN_SLEEP_DURATION
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SLEEP_DURATION,
                    max=MAX_SLEEP_DURATION,
                    step=5,
                    mode=NumberSelectorMode.SLIDER,
                    unit_of_measurement="min",
                )
            ),
        }
    )


class SleepTrackingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sleep Tracking."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SleepTrackingOptionsFlow:
        return SleepTrackingOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input.get(CONF_PERSON_NAME, "").strip()
            if not name:
                errors[CONF_PERSON_NAME] = "name_required"
            else:
                await self.async_set_unique_id(f"{DOMAIN}_{name.casefold()}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={**user_input, CONF_PERSON_NAME: name},
                    options={
                        CONF_INTERRUPTION_THRESHOLD: DEFAULT_INTERRUPTION_THRESHOLD,
                        CONF_MIN_SLEEP_DURATION: DEFAULT_MIN_SLEEP_DURATION,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_data_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            name = user_input.get(CONF_PERSON_NAME, "").strip()
            if not name:
                errors[CONF_PERSON_NAME] = "name_required"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**user_input, CONF_PERSON_NAME: name},
                    title=name,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_data_schema(entry.data),
            errors=errors,
        )


class SleepTrackingOptionsFlow(OptionsFlow):
    """Handle options for Sleep Tracking."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(self.config_entry.options),
        )
