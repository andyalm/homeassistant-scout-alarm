# polling is limited to every 15 minutes to avoid being rate-limited
from datetime import timedelta
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant

from .const import ATTRIBUTION, DOMAIN, LOGGER

SCAN_INTERVAL = timedelta(seconds=900)

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "temperature": [
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        "-T",
        "(T)",
        SensorStateClass.MEASUREMENT,
    ],
    "humidity": [
        PERCENTAGE,
        SensorDeviceClass.HUMIDITY,
        "-H",
        "(H)",
        SensorStateClass.MEASUREMENT,
    ],
}


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up entry."""
    _LOGGER.debug("Calling async_setup_entry")
    entities = []
    scout_alarm = hass.data[DOMAIN]
    location_api = scout_alarm.location_api

    devices = await location_api.get_devices()

    for d in devices:
        _name = d["name"]
        # is the device a temperature sensor?
        if d["reported"].get("temperature"):
            LOGGER.info(f"Creating temperature sensor: {_name}")
            entities.append(
                ScoutSensor(d, "temperature", scout_alarm.location_api, config_entry)
            )
        # is the device a humidity sensor?
        if d["reported"].get("humidity"):
            LOGGER.info(f"Creating humidity sensor: {_name}")
            entities.append(
                ScoutSensor(d, "humidity", scout_alarm.location_api, config_entry)
            )

    async_add_entities(entities)

    return True


class ScoutSensor(SensorEntity):
    def __init__(self, device, data_key, location_api, config_entry) -> None:
        self._device = device
        self._data_key = data_key
        self._api = location_api
        self._config_entry = config_entry

    @property
    def unique_id(self):
        """Return the unique ID which is the device ID with an appropriate suffix to make it unique."""
        return self._device["id"] + SENSOR_TYPES.get(self._data_key)[2]

    @property
    def name(self):
        """Return the device name, including the type as a prefix."""
        return self._device["name"]

    @property
    def available(self) -> bool:
        if self._device.get("reported"):
            return self._device["reported"].get("timedout") is not True
        else:
            return True

    @property
    def device_class(self):
        """Return the device class of this entity."""
        return (
            SENSOR_TYPES.get(self._data_key)[1]
            if self._data_key in SENSOR_TYPES
            else None
        )

    @property
    def state_class(self):
        """Return the state class of this entity."""
        return (
            SENSOR_TYPES.get(self._data_key)[4]
            if self._data_key in SENSOR_TYPES
            else None
        )

    @property
    def native_value(self):
        """Return the value of the sensor in its native measurement (unconverted)."""
        return (
            round(self._device["reported"]["temperature"].get("degrees"))
            if self._data_key == "temperature"
            else self._device["reported"]["humidity"].get("percent")
        )

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        try:
            return SENSOR_TYPES.get(self._data_key)[0]
        except TypeError:
            return None

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def force_update(self) -> bool:
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
            f"{self.name} ({self._data_key}) updating with new Device data: {updated_data}"
        )
        if updated_data.get("status") != 429:
            self._device = updated_data
        else:
            LOGGER.warning(
                f"rate-limited exceeded when updating {self.name} ({self._data_key})"
            )
