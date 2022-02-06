#!/bin/sh

# Install requirements from user-provided pip file
REQUIREMENTS_FILE=/config/requirements.txt
if test -f "$REQUIREMENTS_FILE"; then
    echo "$REQUIREMENTS_FILE exists, installing requirements."
    python3 -m pip install -r $REQUIREMENTS_FILE
fi

# Pull in latest config from user
FILE=/config/mopidy.conf
if test -f "$FILE"; then
    echo "$FILE exists, using as command line argument"
    mopidy --config $FILE
else
    mopidy
fi