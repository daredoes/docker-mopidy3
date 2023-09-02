# Dev Notes

## Disclaimer

I don't know read and use at your own peril or something. "Dead men push no commits".

## Goals

- Create first time setup UI
- Allow choosing path for snapcast pipe
- Fix when snapcast pipe breaks


## How this works

1. The dockerfile installs the minimums for Mopidy (with youtube and some other stuff) and Supervisor without starting either. It installs some minimum python requirements, and copies over some needed files. There is also a custom sed hack to allow the library to be scanned from Iris
2. The entrypoint runs a bash script triggering a python script that creates a supervisord configuration entry for each object in the `server` object in `servers.json`. This configuration file contains information about what unique information pertains to the instance stored as environment variables.
3. Supervisor starts on port 9001. This kicks off a library scan from `scan_library.sh` using `/etc/mopidy/mopidy.conf`, and starts each of the instances from mopidy.
4. An instance starts by executing `start_mopidy.sh`. This logs some information to the console, and then tries to install the contents of the `requirements.txt` file using the path from the environment variable `REQUIREMENTS_FILE`. Then `start.py` is triggered to kill anything already running on the desired ports, remove any streams on snapcast with the same ID, and send snapcast information about our new stream.
5. Mopidy runs! If it can't be found on the given web port, there is probably an issue in the `mopidy.conf` like a disabled line. Note: adding `;` to a line makes the entire line invalid.
