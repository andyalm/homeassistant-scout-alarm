from copy import deepcopy
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import (
    SOURCE_IMPORT,
    ConfigEntry
)

from .const import (
    DOMAIN,
    LOGGER,
    DATA_SCOUT_CONFIG,
    CONF_MODES
)

from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_NIGHT
)

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .api.scout_api import ScoutApi, ScoutLocationApi
from .api.scout_session import ScoutSession
from .api.scout_listener import ScoutListener

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
                        vol.Optional(STATE_ALARM_ARMED_NIGHT): cv.string
                    }
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SCOUT_PLATFORMS = [
    'alarm_control_panel'
]


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
    LOGGER.info("async_setup_entry from __init__ called")

    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    mode_map = config_entry.data[CONF_MODES]

    scout_alarm = ScoutAlarm(username, password, mode_map)
    await scout_alarm.listener.async_connect()
    hass.data[DOMAIN] = scout_alarm

    for platform in SCOUT_PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


# class ScoutAlarmConfigFlow(ConfigFlow, domain=DOMAIN):
#     async def async_step_user(self, info):
#         if info is not None:
#             pass  # TODO: process info
#
#         await self._async_handle_discovery_without_unique_id()
#
#         return self.async_show_form(
#             #step_id="user", data_schema=vol.Schema({vol.Required("password"): str})
#             step_id="zeroconf"
#         )

class ScoutAlarm:
    def __init__(self, username, password, state_to_mode_map):
        self.session = ScoutSession(username, password)
        self.api = ScoutApi(self.session)
        self.location_api = ScoutLocationApi(self.api)
        self.listener = ScoutListener(self.session)
        self.state_to_mode_map = state_to_mode_map
