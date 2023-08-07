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
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_VIBRATION,
    DEVICE_CLASS_LOCK,
    DEVICE_CLASS_SAFETY
)

from .const import (
    DOMAIN,
    ATTRIBUTION,
    LOGGER,
    SCOUT_DEVICE_STATE_OPEN,
    SCOUT_DEVICE_STATE_WET,
    SCOUT_DEVICE_STATE_MOTION_START,
    SCOUT_DEVICE_STATE_OK,
    SCOUT_DEVICE_STATE_LOCKED,
    SCOUT_DEVICE_STATE_UNLOCKED,
    SCOUT_DEVICE_TYPE_DOOR_PANEL,
    SCOUT_DEVICE_TYPE_ACCESS_SENSOR,
    SCOUT_DEVICE_TYPE_MOTION_SENSOR,
    SCOUT_DEVICE_TYPE_SMOKE_ALARM,
    SCOUT_DEVICE_TYPE_CO_DETECTOR,
    SCOUT_DEVICE_TYPE_WATER_SENSOR,
    SCOUT_DEVICE_TYPE_GLASS_BREAK,
    SCOUT_DEVICE_TYPE_DOOR_LOCK
)

SUPPORTED_SCOUT_DEVICE_TYPES = [
    SCOUT_DEVICE_TYPE_DOOR_PANEL,
    SCOUT_DEVICE_TYPE_ACCESS_SENSOR,
    SCOUT_DEVICE_TYPE_MOTION_SENSOR,
    SCOUT_DEVICE_TYPE_SMOKE_ALARM,
    SCOUT_DEVICE_TYPE_WATER_SENSOR,
    SCOUT_DEVICE_TYPE_GLASS_BREAK,
    SCOUT_DEVICE_TYPE_DOOR_LOCK
]


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry, async_add_entities):
    """Set up entry."""
    entities = []
    scout_alarm = hass.data[DOMAIN]
    location_api = scout_alarm.location_api

    devices = await location_api.get_devices()
    for d in devices:
      type = d['type']
      name = d['name']
      if type in SUPPORTED_SCOUT_DEVICE_TYPES:
        """Create two devices if this is a combo smoke/co device"""
        LOGGER.info(f'creating binary sensor for {type} named {name}')
        if type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
          trigger = d['reported']['trigger']
          state = trigger['state']
          if state.get('smoke'):
            entities.append(
              ScoutDoorWindowSensor(d, SCOUT_DEVICE_TYPE_SMOKE_ALARM, scout_alarm.location_api, scout_alarm.listener)
            )
          elif state.get('co'):
            entities.append(
              ScoutDoorWindowSensor(d, SCOUT_DEVICE_TYPE_CO_DETECTOR, scout_alarm.location_api, scout_alarm.listener)
            )
          else:
            LOGGER.warn(f'Cannot determine smoke detector type.  Device data: {d}')
        else:
          entities.append(
            ScoutDoorWindowSensor(d, type, scout_alarm.location_api, scout_alarm.listener)
          )
      else:
        LOGGER.warn(f'Invalid binary sensor type: {type}.  Device data: {d}')

    async_add_entities(
        entities, False
    )

    return True


class ScoutDoorWindowSensor(binary_sensor.BinarySensorEntity):
    def __init__(self, device, type, location_api, listener):
        self._device = device
        self._type = type
        self._api = location_api
        self._listener = listener
        self._listener.on_device_change(self.__on_device_change)

    @property
    def unique_id(self):
        device_type = self._type
        if device_type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
          id =  self._device['id'] + "-SA"
        elif device_type == SCOUT_DEVICE_TYPE_CO_DETECTOR:
          id =  self._device['id'] + "-CO"
        else:
          id = self._device['id']
        return id

    @property
    def name(self):
        return self._device['name']

    @property
    def available(self) -> bool:
        if self._device.get('reported'):
            return self._device['reported'].get('timedout') is not True
        else:
            return True

    @property
    def is_on(self):
        trigger = self.reported_trigger()
        if not trigger:
            return False

        device_type = self._type
        on_state = False
        if device_type == SCOUT_DEVICE_TYPE_DOOR_PANEL:
            on_state = (trigger['state'] == SCOUT_DEVICE_STATE_OPEN)
        elif device_type == SCOUT_DEVICE_TYPE_ACCESS_SENSOR:
            on_state = (trigger['state'] == SCOUT_DEVICE_STATE_OPEN)
        elif device_type == SCOUT_DEVICE_TYPE_MOTION_SENSOR:
            on_state = (trigger['state'] == SCOUT_DEVICE_STATE_MOTION_START)
        elif device_type == SCOUT_DEVICE_TYPE_WATER_SENSOR:
            on_state = (trigger['state'] == SCOUT_DEVICE_STATE_WET)
        elif device_type == SCOUT_DEVICE_TYPE_GLASS_BREAK:
            on_state = (trigger['state'] != SCOUT_DEVICE_STATE_OK)
        elif device_type == SCOUT_DEVICE_TYPE_DOOR_LOCK:
            on_state = (trigger['state'] == SCOUT_DEVICE_STATE_UNLOCKED)
        elif device_type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
            on_state = (trigger['state']['smoke'] != SCOUT_DEVICE_STATE_OK)
        elif device_type == SCOUT_DEVICE_TYPE_CO_DETECTOR:
            on_state = (trigger['state']['co'] != SCOUT_DEVICE_STATE_OK)
        return on_state

    @property
    def device_class(self):
        device_type = self._type
        if device_type == SCOUT_DEVICE_TYPE_DOOR_PANEL:
            return DEVICE_CLASS_DOOR
        elif device_type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
            return DEVICE_CLASS_SMOKE
        elif device_type == SCOUT_DEVICE_TYPE_CO_DETECTOR:
            return DEVICE_CLASS_SAFETY
        elif device_type == SCOUT_DEVICE_TYPE_MOTION_SENSOR:
            return DEVICE_CLASS_MOTION
        elif device_type == SCOUT_DEVICE_TYPE_WATER_SENSOR:
            return DEVICE_CLASS_MOISTURE
        elif device_type == SCOUT_DEVICE_TYPE_GLASS_BREAK:
            return DEVICE_CLASS_VIBRATION
        elif device_type == SCOUT_DEVICE_TYPE_DOOR_LOCK:
            return DEVICE_CLASS_LOCK
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
    def extra_state_attributes(self):
        """Return the state attributes."""
        battery = self._device['reported'].get('battery')
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "device_id": self._device['id'],
            "device_type": self._device['type'],
            "battery_low": battery.get('low') if battery else False
        }

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "identifiers": {(DOMAIN, self._device['id'])},
            "manufacturer": self._device['reported'].get('manufacturer'),
            "name": self.name,
            "sw_version": self._device['reported'].get('fw_version'),
            "model": self._device['reported'].get('model')
        }

    async def async_update(self):
        """Update device state."""
        updated_data = await self._api.get_device(self._device['id'])
        LOGGER.debug(f'{self.name} updating with new Device data: {updated_data}')
        if updated_data.get('status') != 429:
            self._device = updated_data
        else:
            LOGGER.warn(f'rate-limited exceeded when updating {self.name}')

    def reported_trigger(self):
        reported = self._device.get('reported')
        if not reported:
            return None

        return reported.get('trigger')

    def __on_device_change(self, data):
        if data['id'] == self._device['id']:
            LOGGER.debug(f'{self.name} device change with new Device data: {data}')
            self._device = data
            self.schedule_update_ha_state(force_refresh=False)
