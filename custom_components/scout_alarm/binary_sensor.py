"""Support for Scout Alarm Security System."""

from homeassistant.components import binary_sensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant

from .const import (
    ATTRIBUTION,
    DOMAIN,
    LOGGER,
    SCOUT_DEVICE_STATE_MOTION_START,
    SCOUT_DEVICE_STATE_OK,
    SCOUT_DEVICE_STATE_OPEN,
    SCOUT_DEVICE_STATE_UNLOCKED,
    SCOUT_DEVICE_STATE_WET,
    SCOUT_DEVICE_TYPE_ACCESS_SENSOR,
    SCOUT_DEVICE_TYPE_CO_DETECTOR,
    SCOUT_DEVICE_TYPE_DOOR_LOCK,
    SCOUT_DEVICE_TYPE_DOOR_PANEL,
    SCOUT_DEVICE_TYPE_GLASS_BREAK,
    SCOUT_DEVICE_TYPE_MOTION_SENSOR,
    SCOUT_DEVICE_TYPE_SMOKE_ALARM,
    SCOUT_DEVICE_TYPE_WATER_SENSOR,
)

SUPPORTED_SCOUT_DEVICE_TYPES = [
    SCOUT_DEVICE_TYPE_DOOR_PANEL,
    SCOUT_DEVICE_TYPE_ACCESS_SENSOR,
    SCOUT_DEVICE_TYPE_MOTION_SENSOR,
    SCOUT_DEVICE_TYPE_SMOKE_ALARM,
    SCOUT_DEVICE_TYPE_WATER_SENSOR,
    SCOUT_DEVICE_TYPE_GLASS_BREAK,
    SCOUT_DEVICE_TYPE_DOOR_LOCK,
]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up entry."""
    entities = []
    scout_alarm = hass.data[DOMAIN]
    location_api = scout_alarm.location_api

    devices = await location_api.get_devices()
    for d in devices:
        LOGGER.debug("Found device: %s", d)
        _type = d["type"]
        _name = d["name"]
        if _type in SUPPORTED_SCOUT_DEVICE_TYPES:
            # Create two devices if this is a combo smoke/co device
            LOGGER.debug("Creating binary sensor for %s named %s", _type, _name)
            if _type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
                trigger = d["reported"]["trigger"]
                state = trigger["state"]
                if state.get("smoke"):
                    entities.append(
                        ScoutDoorWindowSensor(
                            d,
                            SCOUT_DEVICE_TYPE_SMOKE_ALARM,
                            scout_alarm.location_api,
                            scout_alarm.listener,
                        )
                    )
                elif state.get("co"):
                    entities.append(
                        ScoutDoorWindowSensor(
                            d,
                            SCOUT_DEVICE_TYPE_CO_DETECTOR,
                            scout_alarm.location_api,
                            scout_alarm.listener,
                        )
                    )
                else:
                    LOGGER.warning(
                        "Cannot determine smoke detector type.  Device data: %s", d
                    )
            else:
                entities.append(
                    ScoutDoorWindowSensor(
                        d, _type, scout_alarm.location_api, scout_alarm.listener
                    )
                )
        else:
            LOGGER.warning("Invalid binary sensor type: %s. Device data: %s", _type, d)

    async_add_entities(entities, False)

    return True


class ScoutDoorWindowSensor(binary_sensor.BinarySensorEntity):
    """Representation of the Scout Door and Window Binary Sensor."""

    def __init__(self, device, _type, location_api, listener) -> None:
        """Initialize the door and window sensor."""
        self._device = device
        self._type = _type
        self._api = location_api
        self._listener = listener
        self._listener.on_device_change(self.__on_device_change)

    @property
    def unique_id(self):
        """Return the entity's unique ID."""
        device_type = self._type
        if device_type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
            _id = self._device["id"] + "-SA"
        elif device_type == SCOUT_DEVICE_TYPE_CO_DETECTOR:
            _id = self._device["id"] + "-CO"
        else:
            _id = self._device["id"]
        return _id

    @property
    def name(self):
        """Return the entity name."""
        return self._device["name"]

    @property
    def available(self) -> bool:
        """Return entity availability."""
        if self._device.get("reported"):
            return self._device["reported"].get("timedout") is not True
        else:
            return True

    @property
    def is_on(self):
        """Return whether the device is on."""
        trigger = self.reported_trigger()
        if not trigger:
            return False

        device_type = self._type
        on_state = False
        if device_type == SCOUT_DEVICE_TYPE_DOOR_PANEL:
            on_state = trigger["state"] == SCOUT_DEVICE_STATE_OPEN
        elif device_type == SCOUT_DEVICE_TYPE_ACCESS_SENSOR:
            on_state = trigger["state"] == SCOUT_DEVICE_STATE_OPEN
        elif device_type == SCOUT_DEVICE_TYPE_MOTION_SENSOR:
            on_state = trigger["state"] == SCOUT_DEVICE_STATE_MOTION_START
        elif device_type == SCOUT_DEVICE_TYPE_WATER_SENSOR:
            on_state = trigger["state"] == SCOUT_DEVICE_STATE_WET
        elif device_type == SCOUT_DEVICE_TYPE_GLASS_BREAK:
            on_state = trigger["state"] != SCOUT_DEVICE_STATE_OK
        elif device_type == SCOUT_DEVICE_TYPE_DOOR_LOCK:
            on_state = trigger["state"] == SCOUT_DEVICE_STATE_UNLOCKED
        elif device_type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
            on_state = trigger["state"]["smoke"] != SCOUT_DEVICE_STATE_OK
        elif device_type == SCOUT_DEVICE_TYPE_CO_DETECTOR:
            on_state = trigger["state"]["co"] != SCOUT_DEVICE_STATE_OK
        return on_state

    @property
    def device_class(self):
        """Return the entity's device class."""
        device_type = self._type
        if device_type == SCOUT_DEVICE_TYPE_DOOR_PANEL:
            return binary_sensor.BinarySensorDeviceClass.DOOR
        elif device_type == SCOUT_DEVICE_TYPE_SMOKE_ALARM:
            return binary_sensor.BinarySensorDeviceClass.SMOKE
        elif device_type == SCOUT_DEVICE_TYPE_CO_DETECTOR:
            return binary_sensor.BinarySensorDeviceClass.SAFETY
        elif device_type == SCOUT_DEVICE_TYPE_MOTION_SENSOR:
            return binary_sensor.BinarySensorDeviceClass.MOTION
        elif device_type == SCOUT_DEVICE_TYPE_WATER_SENSOR:
            return binary_sensor.BinarySensorDeviceClass.MOISTURE
        elif device_type == SCOUT_DEVICE_TYPE_GLASS_BREAK:
            return binary_sensor.BinarySensorDeviceClass.VIBRATION
        elif device_type == SCOUT_DEVICE_TYPE_DOOR_LOCK:
            return binary_sensor.BinarySensorDeviceClass.LOCK
        elif "door" in self._device["name"].lower():
            return binary_sensor.BinarySensorDeviceClass.DOOR
        elif "window" in self._device["name"].lower():
            return binary_sensor.BinarySensorDeviceClass.WINDOW
        else:
            return binary_sensor.BinarySensorDeviceClass.OPENING

    @property
    def should_poll(self) -> bool:
        """Return whether the entity should poll."""
        return False

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        battery = self._device["reported"].get("battery")
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "device_id": self._device["id"],
            "device_type": self._device["type"],
            "battery_low": battery.get("low") if battery else False,
        }

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "identifiers": {(DOMAIN, self._device["id"])},
            "manufacturer": self._device["reported"].get("manufacturer"),
            "name": self.name,
            "sw_version": self._device["reported"].get("fw_version"),
            "model": self._device["reported"].get("model"),
        }

    async def async_update(self):
        """Update device state."""
        updated_data = await self._api.get_device(self._device["id"])
        LOGGER.debug(
            "Binary sensor %s updating with new Device data: %s",
            self.name,
            updated_data,
        )
        if updated_data.get("status") != 429:
            self._device = updated_data
        else:
            LOGGER.warning("Rate-limited exceeded when updating %s", self.name)

    def reported_trigger(self):
        """Return the trigger variable."""
        reported = self._device.get("reported")
        if not reported:
            return None

        return reported.get("trigger")

    def __on_device_change(self, data):
        """Trigger upon device change."""
        if data["id"] == self._device["id"]:
            LOGGER.debug("%s device change with new Device data: %s", self.name, data)
            self._device = data
            self.schedule_update_ha_state(force_refresh=False)
