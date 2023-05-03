#!/bin/sh
IRIS_DIR=$(pip3 show mopidy_iris | grep Location: | sed 's/^.\{10\}//')

bash $IRIS_DIR/mopidy_iris/system.sh local_scan