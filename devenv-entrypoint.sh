#!/usr/bin/env bash

ln -s /src/scout-alarm/custom_components /src/core/config/custom_components

cd /src/core || exit
#{
#  echo "scout_alarm:"
#  echo "  username: $SCOUT_USERNAME"
#  echo "  password: $SCOUT_PASSWORD"
#  echo "  modes:"
#  echo "    armed_away: Away"
#echo "    armed_home: Upstairs"
#  echo "    armed_night: Sleep"
#} >> config/configuration.yaml
source venv/bin/activate

CMD=$1
if [[ "$CMD" != "" ]]; then
  echo "exec $*"
  exec "$@"
else
  exec hass -c config
fi

