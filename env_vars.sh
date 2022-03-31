#!/bin/sh

if [ -z "$XDG_CONFIG_DIR" ]; then
	echo "XDG_CONFIG_DIR=/config"
else
	echo "XDG_CONFIG_DIR=$XDG_CONFIG_DIR"
fi

if [ -z "$XDG_CACHE_DIR" ]; then
	echo "XDG_CACHE_DIR=/config/cache"
else
	echo "XDG_CACHE_DIR=$XDG_CACHE_DIR"
fi

if [ -z "$XDG_DATA_DIR" ]; then
	echo "XDG_DATA_DIR=/config/data"
else
	echo "XDG_DATA_DIR=$XDG_DATA_DIR"
fi

if [ -z "$XDG_RUNTIME_DIR" ]; then
	echo "XDG_RUNTIME_DIR=/tmp/"
else
	echo "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
fi

echo "LOADED_ENV=true"