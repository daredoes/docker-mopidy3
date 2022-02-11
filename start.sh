#!/bin/sh

# Install requirements from user-provided pip file
REQUIREMENTS_FILE=/config/requirements.txt
if test -f "$REQUIREMENTS_FILE"; then
    echo "$REQUIREMENTS_FILE exists, installing requirements."
    python3 -m pip install -r $REQUIREMENTS_FILE
fi

python3 /start.py start

#Define cleanup procedure
cleanup() {
    echo "Container stopped, performing cleanup..."
    python3 /start.py stop
}
#Trap SIGTERM
# trap 'cleanup' TERM

# python3 /start.py stop & 
/usr/bin/supervisord