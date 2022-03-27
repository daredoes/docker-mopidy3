#!/bin/sh

python3 /start.py create-supervisord-conf

# Exit all child processes properly
shutdown () {
  echo "Trapped SIGTERM/SIGINT/x so shutting down supervisord gracefully..."
  kill $SUPERVISOR_PID
  wait $SUPERVISOR_PID
  exit 0
}

trap shutdown HUP TERM INT

export XDG_CACHE_DIR=/config/cache
export XDG_CONFIG_DIR=/config
export XDG_DATA_DIR=/config/data
export XDG_RUNTIME_DIR=/tmp/
/usr/bin/supervisord -c /etc/supervisord.conf &
SUPERVISOR_PID=$!

wait "${SUPERVISOR_PID}"