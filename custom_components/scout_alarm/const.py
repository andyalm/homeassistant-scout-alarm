"""Constants for the Scout Alarm Security System component."""
import logging

LOGGER = logging.getLogger(__package__)

DOMAIN = "scout_alarm"
DATA_SCOUT_CONFIG = "scout_alarm_config"
ATTRIBUTION = "Data provided by api.scoutalarm.com"

CONF_MODES = "modes"

SCOUT_MODE_ARMED = "armed"
SCOUT_MODE_ARMING = "arming"
SCOUT_MODE_DISARMED = "disarmed"
SCOUT_MODE_ALARMED = "alarmed"

SCOUT_MODE_EVENT_DISMISSED = "dismissed"
SCOUT_MODE_EVENT_ALARMED = "alarmed"
SCOUT_MODE_EVENT_TRIGGERED = "triggered"

SCOUT_DEVICE_STATE_OPEN = "open"
SCOUT_DEVICE_STATE_CLOSE = "close"
SCOUT_DEVICE_STATE_MOTION_START = "motion_start"
SCOUT_DEVICE_STATE_MOTION_STOP = "motion_stop"
SCOUT_DEVICE_STATE_DRY = "dry"
SCOUT_DEVICE_STATE_WET = "wet"
SCOUT_DEVICE_STATE_BREAK ="break"
SCOUT_DEVICE_STATE_OK = "ok"

SCOUT_DEVICE_TYPE_DOOR_PANEL = "door_panel"
SCOUT_DEVICE_TYPE_ACCESS_SENSOR = "access_sensor"
SCOUT_DEVICE_TYPE_MOTION_SENSOR = "motion_sensor"
SCOUT_DEVICE_TYPE_SMOKE_ALARM = "smoke_alarm"
SCOUT_DEVICE_TYPE_WATER_SENSOR = "water_sensor"
SCOUT_DEVICE_TYPE_GLASS_BREAK = "glass_break"
