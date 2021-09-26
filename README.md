# Scout Alarm for Home Assistant

A Scout Alarm Integration for Home Assistant.

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

## What works

- An `alarm_control_panel` entity is created whose state will reflect that of your scout alarm.
- `binary_sensor`'s are added for each `door_panel`, `access_sensor`, `motion_sensor`, `smoke_alarm`, `water_sensor`, `glass_break`, and `lock` device.
- `sensor`'s are added to track temperature and humidity for devices that support it.

## Unplanned but would accept contributions

 - Cameras. (We don't have a way to test cameras at this time)

