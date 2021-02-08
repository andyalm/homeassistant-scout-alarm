import json
from homeassistant.config_entries import ConfigEntry

import homeassistant.components.binary_sensor as binary_sensor

from homeassistant.helpers.typing import (
    HomeAssistantType
)

from homeassistant.const import (
    ATTR_ATTRIBUTION
)

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_WINDOW,
    DEVICE_CLASS_OPENING,
    DEVICE_CLASS_SMOKE,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_MOISTURE
)

from .const import (
    DOMAIN,
    ATTRIBUTION,
    LOGGER,
    SCOUT_DEVICE_STATE_OPEN,
    SCOUT_DEVICE_TYPE_DOOR_PANEL,
    SCOUT_DEVICE_TYPE_ACCESS_SENSOR,
    SCOUT_DEVICE_TYPE_MOTION_SENSOR,
    SCOUT_DEVICE_TYPE_SMOKE_ALARM,
    SCOUT_DEVICE_TYPE_WATER_SENSOR
)

SUPPORTED_SCOUT_DEVICE_TYPES = [
    SCOUT_DEVICE_TYPE_DOOR_PANEL,
    SCOUT_DEVICE_TYPE_ACCESS_SENSOR,
    SCOUT_DEVICE_TYPE_MOTION_SENSOR,
    SCOUT_DEVICE_TYPE_SMOKE_ALARM,
    SCOUT_DEVICE_TYPE_WATER_SENSOR
]


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry, async_add_entities):
    """Set up entry."""

    scout_alarm = hass.data[DOMAIN]
    location_api = scout_alarm.location_api

    devices = await location_api.get_devices()
    entities = [ScoutDoorWindowSensor(d, scout_alarm.location_api, scout_alarm.listener) for d in devices if d['type'] in SUPPORTED_SCOUT_DEVICE_TYPES]

    """Set up Scout Alarm control panel device."""
    async_add_entities(
        entities, False
    )

    return True


class ScoutDoorWindowSensor(binary_sensor.BinarySensorEntity):
    def __init__(self, device, location_api, listener):
        self._device = device
        self._api = location_api
        self._listener = listener
        self._listener.on_device_change(self.__on_device_change)

    @property
    def unique_id(self):
        return self._device['id']

    @property
    def name(self):
        return self._device['name']

    @property
    def is_on(self):
        trigger = self.reported_trigger()
        if not trigger:
            return False

        return trigger['state'] == SCOUT_DEVICE_STATE_OPEN

    @property
    def device_class(self):
        device_type = self._device['type']
        if device_type == SCOUT_DEVICE_TYPE_DOOR_PANEL:
            return DEVICE_CLASS_DOOR
        elif device_type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
            return DEVICE_CLASS_SMOKE
        elif device_type == SCOUT_DEVICE_TYPE_MOTION_SENSOR:
            return DEVICE_CLASS_MOTION
        elif device_type == SCOUT_DEVICE_TYPE_WATER_SENSOR:
            return DEVICE_CLASS_MOISTURE
        elif "door" in self._device['name'].lower():
            return DEVICE_CLASS_DOOR
        elif "window" in self._device['name'].lower():
            return DEVICE_CLASS_WINDOW
        else:
            return DEVICE_CLASS_OPENING

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes."""

        """does device report humidity"""
        check_humidity = self._device['reported'].get('humidity')
        if check_humidity:
            humidity = str(check_humidity.get('percent')) + "%"
        else:
            humidity = "N/A"

        """does device report temperature"""
        check_temp = self._device['reported'].get('temperature')
        if check_temp:
            tempC = round(check_temp.get('degrees'))
            tempF = round(tempC * 1.8 + 32)
            degree_sign = u"\u00B0"
            temp = str(tempC) + degree_sign + "C / " + str(tempF) + degree_sign + "F"
        else:
            temp = "N/A"

        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "device_id": self._device['id'],
            "device_type": self._device['type'],
            "battery_low": self._device['reported']['battery'].get('low'),
            "temperature": temp,
            "humidity": humidity
        }

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "identifiers": {(DOMAIN, self._device['id'])},
            "manufacturer": self._device['reported']['manufacturer'],
            "name": self.name,
            "sw_version": self._device['reported']['fw_version'],
            "model": self._device['reported']['model']
        }

    async def async_update(self):
        """Update device state."""
        LOGGER.info(f'scout_alarm device {self.name} updating...')
        self._device = await self._api.get_device(self._device['id'])

    def reported_trigger(self):
        reported = self._device.get('reported')
        if not reported:
            return None

        return reported.get('trigger')

    def __on_device_change(self, data):
        if data['id'] == self._device['id']:
            self.schedule_update_ha_state(force_refresh=True)
