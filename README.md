# Scout Alarm for Home Assistant

A custom [Scout Alarm](https://www.scoutalarm.com/) Integration for Home Assistant.

## Installation

1. Copy the `custom_components/scout_alarm` directory from this repo to your Home Assistant installation.
2. Add the integration via the UI.

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
