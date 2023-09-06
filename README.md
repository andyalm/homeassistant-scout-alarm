[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/andyalm/homeassistant-scout-alarm.svg)](https://github.com/andyalm/homeassistant-scout-alarm/releases)
[![HA integration usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.scout_alarm.total)](https://analytics.home-assistant.io/custom_integrations.json)

# Scout Alarm for Home Assistant

A custom [Scout Alarm](https://www.scoutalarm.com/) Integration for Home Assistant.

## Installation

You can install this integration via [HACS](#hacs) or [manually](#manual).

### HACS

Search for the Scout Alarm integration and choose install. Reboot Home Assistant and configure the Scout Alarm integration via the integrations page or press the blue button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=scout_alarm)


### Manual

Copy the `custom_components/scout_alarm` to your custom_components folder. Reboot Home Assistant and configure the iKamand integration via the integrations page or press the blue button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=scout_alarm)


### YAML Configuration

If you prefer to configure the integration via YAML instead of the UI, add something like the following to your `configuration.yaml`:

```yaml
scout_alarm:
  username: !secret scout_alarm_username
  password: !secret scout_alarm_password
  modes:
    armed_away: Away #value should match the name of the mode in your Scout system
    armed_home: Perimeter
    armed_night: Night
```

Note that not all modes need to be mapped, but values do need to be unique, so do not map multiple states to the same scout mode.

## Supported Devices

- Door Panel
- Access Sensor
- Motion Sensor
- Smart Smoke and Carbon Monoxide Detector
- Water Sensor
- Glass Break Sensor
- Door Lock

## Unplanned but would accept contributions

- Scout Indoor Camera
- Scout Video Doorbell
- Keypad

## Created Entities

An `alarm_control_panel` entity is created whose state will reflect that of your scout alarm.

A `binary_sensor` entity is created for each supported Scout device.  

A `sensor` entitity is created for Temperature and Humidity for those Scout devices that report on that data. 

For any one Scout device (i.e, Motion Sensor), up to three Entities might be created (the `binary_sensor` for the device and two `sensor`s for temperature and humidity).
