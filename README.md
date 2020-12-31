# Scout Alarm for Home Assistant

An experimental Scout Alarm Integration for Home Assistant.

## Installation

1. Copy the `custom_components/scout_alarm` directory from this repo to your Home Assistant installation.
2. Add the integration via the UI. Or, if you prefer to add via yaml instead, it would look something like the following:

```yaml
scout_alarm:
   username: !secret scout_alarm_username
   password: !secret scout_alarm_password
```

## What works

An `alarm_control_panel` entity is created whose state will reflect that of your scout alarm.

## Planned TODO

 - Add support for door/window sensors

## Unplanned but would accept contributions

 - Camera and other device type support

