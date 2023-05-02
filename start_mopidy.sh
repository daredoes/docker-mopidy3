#!/bin/sh

if [ -z "$XDG_CONFIG_DIR" ]; then
	echo "export XDG_CONFIG_DIR=/config"
	export XDG_CONFIG_DIR=/config
else
	echo "export XDG_CONFIG_DIR=$XDG_CONFIG_DIR"
	export XDG_CONFIG_DIR=$XDG_CONFIG_DIR
fi

if [ -z "$XDG_CACHE_DIR" ]; then
	echo "export XDG_CACHE_DIR=/config/cache"
	export XDG_CACHE_DIR=/config/cache
else
	echo "export XDG_CACHE_DIR=$XDG_CACHE_DIR"
	export XDG_CACHE_DIR=$XDG_CACHE_DIR
fi

if [ -z "$XDG_DATA_DIR" ]; then
	echo "export XDG_DATA_DIR=/config/data"
	export XDG_DATA_DIR=/config/data
else
	echo "export XDG_DATA_DIR=$XDG_DATA_DIR"
	export XDG_DATA_DIR=$XDG_DATA_DIR
fi

if [ -z "$XDG_RUNTIME_DIR" ]; then
	echo "export XDG_RUNTIME_DIR=/tmp/"
	export XDG_RUNTIME_DIR=/tmp/
else
	echo "export XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
	export XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR
fi

if [ -z "$LOADED_ENV" ]; then
	echo "export LOADED_ENV=true"
	export LOADED_ENV=true
fi

printenv
echo "Has arguments $STREAM_ID and $CONFIG_FILEPATH"
# Install requirements from user-provided pip file
REQUIREMENTS_FILE=/config/requirements.txt
if test -f "$REQUIREMENTS_FILE"; then
    echo "$REQUIREMENTS_FILE exists, installing requirements."
    python3 -m pip install -r $REQUIREMENTS_FILE
fi

# Exit all child processes properly
shutdown () {
  echo "Trapped SIGTERM/SIGINT/x so cleaning up $STREAM_ID..."
  python3 /start.py cleanup --stream-id "$STREAM_ID"
  exit 0
}

trap shutdown HUP TERM INT

python3 /start.py create --stream-id "$STREAM_ID"

/usr/bin/mopidy --config $CONFIG_FILEPATH &
MOPIDY_PID=$!

wait "${MOPIDY_PID}"