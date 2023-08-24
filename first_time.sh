#!/bin/sh

if [ -f "/IS_CONTAINER" ]; then
	IS_CONTAINER=true
else
	IS_CONTAINER=false
fi
