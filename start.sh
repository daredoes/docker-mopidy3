#!/bin/sh

python3 /start.py build

# Exit all child processes properly
shutdown () {
  echo "Trapped SIGTERM/SIGINT/x so shutting down supervisord gracefully..."
  kill $SUPERVISOR_PID
  wait $SUPERVISOR_PID
  exit 0
}

trap shutdown HUP TERM INT

/usr/bin/supervisord &
SUPERVISOR_PID=$!

wait "${SUPERVISOR_PID}"