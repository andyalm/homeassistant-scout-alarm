"""Support for Scout Alarm Security System."""

import asyncio
import json

import homeassistant.components.alarm_control_panel as alarm
from homeassistant.components.alarm_control_panel import (
    ATTR_CHANGED_BY,
    ATTR_CODE_ARM_REQUIRED,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_CODE_FORMAT
)
from homeassistant.core import HomeAssistant

from .api.scout_api import ScoutLocationApi
from .api.scout_listener import ScoutListener
from .const import (
    ATTRIBUTION,
    DOMAIN,
    LOGGER,
    SCOUT_MODE_ALARMED,
    SCOUT_MODE_ARMED,
    SCOUT_MODE_ARMING,
    SCOUT_MODE_EVENT_DISMISSED,
    SCOUT_MODE_EVENT_TRIGGERED,
)

ICON = "mdi:security"


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up entry."""
    scout_alarm = hass.data[DOMAIN]
    async_add_entities(
        [
            ScoutAlarmControlPanel(
                scout_alarm.location_api,
                scout_alarm.listener,
                scout_alarm.state_to_mode_map,
            )
        ],
        True,
    )

    return True


class ScoutAlarmControlPanel(alarm.AlarmControlPanelEntity):
    """An alarm_control_panel implementation for Scout Alarm."""

    def __init__(
        self,
        api: ScoutLocationApi,
        listener: ScoutListener,
        state_to_mode: dict[str, str],
    ) -> None:
        """Initialize the control panel."""
        self.state_to_mode = state_to_mode
        self.mode_to_state = {value: key for key, value in self.state_to_mode.items()}
        self._modes = None
        self._location = None
        self._api = api
        self._listener = listener
        self._listener.on_mode_change(self.__on_mode_changed)
        self._location_channel = None
        self._last_changed_by = None
        self._last_pushed_state = None

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._location["id"] if self._location else None

    @property
    def icon(self):
        """Return the icon."""
        return ICON

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state."""
        if self._modes is None:
            return None

        if self.is_alarmed():
            return AlarmControlPanelState.TRIGGERED

        armed_mode = self.armed_mode()
        if (
            armed_mode
            and self._last_pushed_state
            and self._last_pushed_state["mode_id"] == armed_mode["id"]
            and self._last_pushed_state["event"] == SCOUT_MODE_EVENT_TRIGGERED
        ):
            return AlarmControlPanelState.PENDING

        if armed_mode is not None:
            return self.mode_to_state[armed_mode["name"]] or AlarmControlPanelState.ARMED_AWAY

        arming_mode = self.arming_mode()
        if arming_mode is not None:
            return AlarmControlPanelState.ARMING

        return AlarmControlPanelState.DISARMED

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
        if self.state_to_mode.get(AlarmControlPanelState.ARMED_HOME):
            features |= AlarmControlPanelEntityFeature.ARM_HOME
        if self.state_to_mode.get(AlarmControlPanelState.ARMED_AWAY):
            features |= AlarmControlPanelEntityFeature.ARM_AWAY
        if self.state_to_mode.get(AlarmControlPanelState.ARMED_NIGHT):
            features |= AlarmControlPanelEntityFeature.ARM_NIGHT
        if self.state_to_mode.get(AlarmControlPanelState.ARMED_CUSTOM_BYPASS):
            features |= AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS
        if self.state_to_mode.get(AlarmControlPanelState.ARMED_VACATION):
            features |= AlarmControlPanelEntityFeature.ARM_VACATION

        return features

    @property
    def should_poll(self) -> bool:
        """Return whether the device should poll."""
        return False

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        armed_mode = self.alarmed_mode() or self.armed_mode() or self.arming_mode()
        if armed_mode:
            await self._api.update_mode_state(armed_mode["id"], "disarm")

    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        home_mode = self.__mode_for_state(AlarmControlPanelState.ARMED_HOME)
        if home_mode:
            await self._api.update_mode_state(home_mode["id"], SCOUT_MODE_ARMING)

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        away_mode = self.__mode_for_state(AlarmControlPanelState.ARMED_AWAY)
        if away_mode:
            await self._api.update_mode_state(away_mode["id"], SCOUT_MODE_ARMING)

    async def async_alarm_arm_night(self, code=None):
        """Send arm night command."""
        night_mode = self.__mode_for_state(AlarmControlPanelState.ARMED_NIGHT)
        if night_mode:
            await self._api.update_mode_state(night_mode["id"], SCOUT_MODE_ARMING)

    async def async_alarm_arm_custom_bypass(self, code=None):
        """Send arm bypass command."""
        bypass_mode = self.__mode_for_state(AlarmControlPanelState.ARMED_CUSTOM_BYPASS)
        if bypass_mode:
            await self._api.update_mode_state(bypass_mode["id"], SCOUT_MODE_ARMING)

    async def async_alarm_arm_vacation(self, code=None):
        """Send arm vacation command."""
        vacation_mode = self.__mode_for_state(AlarmControlPanelState.ARMED_VACATION)
        if vacation_mode:
            await self._api.update_mode_state(vacation_mode["id"], SCOUT_MODE_ARMING)

    async def async_update(self):
        """Update device state."""
        LOGGER.debug("scout_alarm panel updating")
        self._modes = await self._api.get_modes()
        self._location = await self._api.get_current_location()
        last_changed_by = self._last_changed_by or "Unknown"
        LOGGER.debug(
            "scout_alarm panel state is %s (last changed by %s",
            self.state,
            last_changed_by,
        )
        if self._location_channel is None:
            self._location_channel = await self._listener.async_add_location(
                self._location["id"]
            )
        if (
            self._last_pushed_state
            and self._last_pushed_state["event"] != SCOUT_MODE_EVENT_TRIGGERED
            and self._last_pushed_state["event"] != SCOUT_MODE_EVENT_DISMISSED
        ):
            expected_state = self.__pop_last_pushed_state()
            mode = next(
                (m for m in self._modes if m["id"] == expected_state["mode_id"]), None
            )
            num_retries = 0
            while mode and mode["state"] != expected_state["event"]:
                LOGGER.warning(
                    "Retrieved state from api did not match the state from the last mode event (last event: '%s', retrieved state: '%s', retries: %s)",
                    expected_state["event"],
                    mode["state"],
                    num_retries,
                )
                await asyncio.sleep(1)
                num_retries += 1
                self._modes = await self._api.get_modes()
                expected_state = self.__pop_last_pushed_state() or expected_state
                mode = next(
                    (m for m in self._modes if m["id"] == expected_state["mode_id"]),
                    None,
                )
                if num_retries >= 30:
                    LOGGER.error(
                        "Scout alarm_control_panel may be out of sync. Expected mode '%s' to have state '%s' but found: %s",
                        expected_state["mode_id"],
                        expected_state["event"],
                        json.dumps(self._modes),
                    )
                    break

    @property
    def name(self):
        """Return the name of the device."""
        return self._location["name"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        mode = self.mode()

        return {
            ATTR_CODE_FORMAT: self.code_format,
            ATTR_CHANGED_BY: self.changed_by,
            ATTR_CODE_ARM_REQUIRED: self.code_arm_required,
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "device_id": self._location["hub_id"],
            "battery_backup": False,
            "cellular_backup": False,
            "scout_mode": mode["name"].strip() if mode else None,
        }

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "identifiers": {(DOMAIN, self._location["id"])},
            "manufacturer": "Scout Alarm",
            "name": self.name,
        }

    def get_mode(self, scout_mode):
        """Return the alarm panel's current mode."""
        armed_modes = [m for m in self._modes if m["state"] == scout_mode]
        if len(armed_modes) == 0:
            return None

        return armed_modes[0]

    def is_alarmed(self):
        """Return whether the alarm panel armed."""
        return self.alarmed_mode() is not None

    def mode(self):
        """Return alarm panel's current mode."""
        return self.alarmed_mode() or self.armed_mode() or self.arming_mode()

    def alarmed_mode(self):
        """Return whether the alarm panel is in Alarmed."""
        return self.get_mode(SCOUT_MODE_ALARMED)

    def armed_mode(self):
        """Return whether the alarm panel is in Armed mode."""
        return self.get_mode(SCOUT_MODE_ARMED)

    def arming_mode(self):
        """Return whether the alarm panel is in Arming mode."""
        return self.get_mode(SCOUT_MODE_ARMING)

    def __mode_for_state(self, state):
        """Return alarm panel's mode for the current state."""
        mode_name = self.state_to_mode.get(state)
        if mode_name is None:
            return None

        matching_modes = [m for m in self._modes if m["name"] == mode_name]
        if len(matching_modes) == 0:
            return None

        return matching_modes[0]

    def __on_mode_changed(self, data):
        """Triggered when the alarm panel mode has changed."""
        affector = data.get("affector")
        if affector:
            last_changed_by = affector.get("name")
            self._last_changed_by = last_changed_by.strip() if last_changed_by else None

        self._last_pushed_state = data
        self.schedule_update_ha_state(force_refresh=True)

    def __pop_last_pushed_state(self):
        """Pop the last pushed state."""
        last_pushed_state = self._last_pushed_state
        self._last_pushed_state = None

        return last_pushed_state
