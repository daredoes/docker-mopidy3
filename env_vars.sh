#!/bin/sh

if [ -z "$XDG_CONFIG_DIR" ]; then
	echo "export XDG_CONFIG_DIR=/config"
else
	echo "export XDG_CONFIG_DIR=$XDG_CONFIG_DIR"
fi

if [ -z "$XDG_CACHE_DIR" ]; then
	echo "export XDG_CACHE_DIR=/config/cache"
else
	echo "export XDG_CACHE_DIR=$XDG_CACHE_DIR"
fi

if [ -z "$XDG_DATA_DIR" ]; then
	echo "export XDG_DATA_DIR=/config/data"
else
	echo "export XDG_DATA_DIR=$XDG_DATA_DIR"
fi

if [ -z "$XDG_RUNTIME_DIR" ]; then
	echo "export XDG_RUNTIME_DIR=/tmp/"
else
	echo "export XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
fi

if [ -z "$LOADED_ENV" ]; then
	echo "export LOADED_ENV=true"
fi

