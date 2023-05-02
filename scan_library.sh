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

whoami

IRIS_DIR=$(pip3 show mopidy_iris | grep Location: | sed 's/^.\{10\}//')

bash $IRIS_DIR/mopidy_iris/system.sh local_scan