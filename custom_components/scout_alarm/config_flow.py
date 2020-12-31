"""Config flow to configure Scout Alarm integration"""

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_HOME
)

from .const import DOMAIN, CONF_MODES

from .api.scout_session import ScoutSession
from .api.scout_api import ScoutApi, ScoutLocationApi

_LOGGER = logging.getLogger(__name__)


class ScoutAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Scout Alarm integration config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    def __init__(self):
        """Initialize flow"""
        self._session = None
        self._username = None
        self._password = None

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if not user_input:
            return self._async_show_auth_form()

        can_auth = False
        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]

            try:
                await self._async_verify_credentials(self._username, self._password)
                can_auth = True
            except:
                errors = {"base": "invalid_auth"}

        if not can_auth:
            return self._async_show_auth_form(errors)

        return await self.async_step_modes()

    async def async_step_modes(self, user_input=None):
        if not user_input:
            return await self._async_show_modes_form()

        night_mode = user_input.get(STATE_ALARM_ARMED_NIGHT)
        away_mode = user_input.get(STATE_ALARM_ARMED_AWAY)
        home_mode = user_input.get(STATE_ALARM_ARMED_HOME)

        if not night_mode and not away_mode and not home_mode:
            return await self._async_show_modes_form(errors={"base": "mode_mapping_required"})

        return self._create_entry(user_input)

    def async_step_import(self, user_input):
        """Import a config flow from configuration."""

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        modes = user_input[CONF_MODES]

        # code for validating login information and error handling needed

        return self.async_create_entry(
            title=f"{username} (from configuration)",
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_MODES: modes
            },
        )

    def _async_show_auth_form(self, errors={}):
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str
                }
            ),
            description_placeholders={"docs_url": "scoutalarm.com"},
            errors=errors)

    def _create_entry(self, user_input):
        data = {
            CONF_USERNAME: self._username,
            CONF_PASSWORD: self._password,
            CONF_MODES: user_input
        }

        return self.async_create_entry(
            title=self._username,
            data=data,
            description_placeholders={"docs_url": "scoutalarm.com"},
        )

    async def _async_verify_credentials(self, username, password):
        self._session = ScoutSession(username, password)
        await self._session.async_get_token()

    async def _async_show_modes_form(self, errors={}):
        scout_modes = await self._async_get_scout_modes()

        return self.async_show_form(
            step_id="modes",
            data_schema=vol.Schema(
                {
                    vol.Optional(STATE_ALARM_ARMED_HOME): vol.In(scout_modes),
                    vol.Optional(STATE_ALARM_ARMED_AWAY): vol.In(scout_modes),
                    vol.Optional(STATE_ALARM_ARMED_NIGHT): vol.In(scout_modes)
                }
            ),
            errors=errors
        )

    async def _async_get_scout_modes(self):
        api = ScoutApi(self._session)
        location_api = ScoutLocationApi(api)
        modes = await location_api.get_modes()

        return [m['name'] for m in modes]




