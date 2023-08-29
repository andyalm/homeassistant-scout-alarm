from copy import deepcopy

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .api.scout_api import ScoutApi, ScoutLocationApi
from .api.scout_listener import ScoutListener
from .api.scout_session import ScoutSession
from .const import CONF_MODES, DATA_SCOUT_CONFIG, DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_MODES): vol.Schema(
                    {
                        vol.Optional(STATE_ALARM_ARMED_AWAY): cv.string,
                        vol.Optional(STATE_ALARM_ARMED_HOME): cv.string,
                        vol.Optional(STATE_ALARM_ARMED_NIGHT): cv.string,
                        vol.Optional(STATE_ALARM_ARMED_CUSTOM_BYPASS): cv.string,
                    }
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SCOUT_PLATFORMS = ["alarm_control_panel", "binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config):
    """Set up Scout Alarm integration."""
    if DOMAIN not in config:
        return True

    scout_config = config[DOMAIN]

    hass.data[DATA_SCOUT_CONFIG] = scout_config

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=deepcopy(scout_config)
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    mode_map = config_entry.data[CONF_MODES]

    scout_alarm = ScoutAlarm(username, password, mode_map, hass)
    await scout_alarm.listener.async_connect()
    hass.data[DOMAIN] = scout_alarm

    for platform in SCOUT_PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


class ScoutAlarm:
    def __init__(
        self, username, password, state_to_mode_map, hass: HomeAssistant
    ) -> None:
        self.session = ScoutSession(username, password)
        self.api = ScoutApi(self.session)
        self.location_api = ScoutLocationApi(self.api)
        self.listener = ScoutListener(self.session, hass.loop)
        self.state_to_mode_map = state_to_mode_map
