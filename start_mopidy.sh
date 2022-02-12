#!/bin/sh

echo "Has arguments $STREAM_ID and $CONFIG_FILEPATH and $COUNT"
# Install requirements from user-provided pip file
REQUIREMENTS_FILE=/config/requirements.txt
if test -f "$REQUIREMENTS_FILE"; then
    echo "$REQUIREMENTS_FILE exists, installing requirements."
    python3 -m pip install -r $REQUIREMENTS_FILE
fi

# Exit all child processes properly
shutdown () {
  echo "Trapped SIGTERM/SIGINT/x so cleaning up $STREAM_ID..."
  python3 /start.py cleanup
  exit 0
}

trap shutdown HUP TERM INT

python3 /start.py create

/usr/bin/mopidy --config $CONFIG_FILEPATH &
MOPIDY_PID=$!

wait "${MOPIDY_PID}"