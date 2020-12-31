"""Support for Scout Alarm Security System alarm control panels."""
from typing import Dict

from homeassistant.config_entries import (
    ConfigEntry
)

import homeassistant.components.alarm_control_panel as alarm
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
)
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_CODE_FORMAT,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    CONF_USERNAME
)
from homeassistant.components.alarm_control_panel import (
    ATTR_CHANGED_BY,
    ATTR_CODE_ARM_REQUIRED
)

from .const import ATTRIBUTION, DOMAIN, LOGGER

from .api.scout_api import ScoutLocationApi
from .api.scout_listener import ScoutListener

ICON = "mdi:security"


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    """Set up entry."""
    username = config_entry.data[CONF_USERNAME]

    scout_alarm = hass.data[DOMAIN]
    """Set up Scout Alarm control panel device."""
    async_add_entities(
        [ScoutAlarmControlPanel(scout_alarm.location_api, scout_alarm.listener, scout_alarm.state_to_mode_map)], True
    )

    return True


class ScoutAlarmControlPanel(alarm.AlarmControlPanelEntity):
    """An alarm_control_panel implementation for Scout Alarm."""

    def __init__(self, api: ScoutLocationApi, listener: ScoutListener, state_to_mode: Dict[str, str]):
        self.state_to_mode = state_to_mode
        self.mode_to_state = {value:key for key, value in self.state_to_mode.items()}
        self._modes = None
        self._location = None
        self._api = api
        self._listener = listener
        self._listener.on_mode_change(self.__on_mode_changed)
        self._location_channel = None
        self._last_changed_by = None

    @property
    def icon(self):
        """Return the icon."""
        return ICON

    @property
    def state(self):
        if self._modes is None:
            return None

        armed_mode = self.armed_mode()
        if armed_mode is not None:
            return self.mode_to_state[armed_mode['name']] or STATE_ALARM_ARMED_AWAY

        arming_mode = self.arming_mode()
        if arming_mode is not None:
            return STATE_ALARM_ARMING

        return STATE_ALARM_DISARMED

    @property
    def changed_by(self):
        """Last change triggered by."""
        return self._last_changed_by

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        return False

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        features = 0
        if self.state_to_mode.get(STATE_ALARM_ARMED_HOME):
            features |= SUPPORT_ALARM_ARM_HOME
        if self.state_to_mode.get(STATE_ALARM_ARMED_AWAY):
            features |= SUPPORT_ALARM_ARM_AWAY
        if self.state_to_mode.get(STATE_ALARM_ARMED_NIGHT):
            features |= SUPPORT_ALARM_ARM_NIGHT

        return features

    @property
    def should_poll(self) -> bool:
        return False

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        armed_mode = self.armed_mode() or self.arming_mode()
        if armed_mode:
            await self._api.update_mode_state(armed_mode['id'], 'disarm')

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        home_mode = self.__mode_for_state(STATE_ALARM_ARMED_HOME)
        if home_mode:
            await self._api.update_mode_state(home_mode['id'], 'arming')

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        away_mode = self.__mode_for_state(STATE_ALARM_ARMED_AWAY)
        if away_mode:
            await self._api.update_mode_state(away_mode['id'], 'arming')

    async def async_alarm_arm_night(self, code=None):
        night_mode = self.__mode_for_state(STATE_ALARM_ARMED_NIGHT)
        if night_mode:
            await self._api.update_mode_state(night_mode['id'], 'arming')

    async def async_update(self):
        """Update device state."""
        LOGGER.info('scout_alarm panel updating...')
        self._modes = await self._api.get_modes()
        self._location = await self._api.get_current_location()
        last_changed_by = self._last_changed_by or 'Unknown'
        LOGGER.info(f"scout_alarm panel state is {self.state} (last changed by {last_changed_by})")
        if self._location_channel is None:
            self._location_channel = await self._listener.async_add_location(self._location['id'])

    @property
    def name(self):
        """Return the name of the device."""
        return self._location['name']

    @property
    def device_state_attributes(self):
        """Return the state attributes."""

        return {
            ATTR_CODE_FORMAT: self.code_format,
            ATTR_CHANGED_BY: self.changed_by,
            ATTR_CODE_ARM_REQUIRED: self.code_arm_required,
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "device_id": self._location['hub_id'],
            "battery_backup": False,
            "cellular_backup": False,
        }

    def armed_mode(self):
        armed_modes = [m for m in self._modes if m['state'] == 'armed']
        if len(armed_modes) == 0:
            return None

        return armed_modes[0]

    def arming_mode(self):
        arming_modes = [m for m in self._modes if m['state'] == 'arming']
        if len(arming_modes) == 0:
            return None

        return arming_modes[0]

    def __mode_for_state(self, state):
        mode_name = self.state_to_mode.get(state)
        if mode_name is None:
            return None

        matching_modes = [m for m in self._modes if m['name'] == mode_name]
        if len(matching_modes) == 0:
            return None

        return matching_modes[0]

    def __on_mode_changed(self, data):
        affector = data.get('affector')
        if affector:
            self._last_changed_by = affector.get('name')
        self.schedule_update_ha_state(force_refresh=True)
