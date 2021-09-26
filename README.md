# Scout Alarm for Home Assistant

An experimental Scout Alarm Integration for Home Assistant.

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
- A `binary_sensor` is created for each of the following supported Scout devices:
  - `door_panel`
  - `access_sensor`
  - `motion_sensor`
  - `smoke_alarm`
  - `water_sensor`
  - `glass_break`
  - `door_lock`
- `temperature` and `humidity` sensors are created for those Scout devices that report on that data

## Unplanned but would accept contributions

 - Scout Camera

