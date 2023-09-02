#!/bin/sh

printenv
echo "Has arguments $STREAM_ID and $CONFIG_FILEPATH and port $TCP_PORT"
# Install requirements from user-provided pip file
if test -f "$REQUIREMENTS_FILE"; then
    echo "$REQUIREMENTS_FILE exists, installing requirements."
    python3 -m pip install -r $REQUIREMENTS_FILE
fi

# IRIS_DIR=$(pip3 show mopidy_iris | grep Location: | sed 's/^.\{10\}//') && sed -i 's/_USE_SUDO = True/_USE_SUDO = False/g' $IRIS_DIR/mopidy_iris/system.py

# Exit all child processes properly
shutdown () {
  echo "Trapped SIGTERM/SIGINT/x so cleaning up $STREAM_ID..."
  python3 /start.py cleanup --stream-id "$STREAM_ID"
  exit 0
}

trap shutdown HUP TERM INT

python3 /start.py create --stream-id "$STREAM_ID" --port "$TCP_PORT"

export IRIS_CONFIG_LOCATION=$CONFIG_FILEPATH

mopidy --config $CONFIG_FILEPATH &
MOPIDY_PID=$!

wait "${MOPIDY_PID}"