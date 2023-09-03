# This container packages [mopidy3](https://mopidy.com)

Comes pre-loaded with spotify, youtube, gstreamer, iris, etc

Built on Ubuntu.

Made because the only other option wasn't working for me :(

## Examples

Run Mopidy3 with in host mode with a `/music` folder in the present working directory, and mapping mopidy's internal data to `/data`:

    docker run --network host -d \
        -v $(pwd)/music:/media \
        -v $(pwd)/data:/home/.local/share/mopidy \
        daredoes/mopidy3

Run Mopidy3 with specified ports with a `/music`` folder in the present working directory:

    docker run --network host -d \
        -p 9001:9001 \
        -p 6680:6680 \
        -p 6600:6600 \
        -p 4953:4953 \
        -v $(pwd)/music:/media \
        -v $(pwd)/data:/home/.local/share/mopidy \
        daredoes/mopidy3

## How It Works

Here's a detailed explanation of how the Mopidy Docker container and its components interact:

1. **Dockerfile Setup**: The Dockerfile sets up the Mopidy environment by installing essential dependencies, including Mopidy with YouTube support, Supervisor, and other required packages. It also copies necessary files into the container. Additionally, a custom sed hack is applied to enable library scanning from Iris.

2. **Entrypoint Execution**: When the Docker container is started, it executes an entrypoint script. This script triggers a Python script responsible for creating a Supervisord configuration entry for each server defined in the `servers.json` file. Each configuration entry stores unique information specific to the instance as environment variables.

3. **Supervisor Initialization**: Supervisor is launched and listens on port 9001. It orchestrates the following tasks:
   - Initiates a library scan using `scan_library.sh` and the configuration from `/etc/mopidy/mopidy.conf`. This step ensures that Mopidy has up-to-date information about available music.
   - Starts each Mopidy instance defined in the Supervisord configuration. These instances are configured based on the environment variables set during entrypoint execution.

4. **Instance Startup**: The Mopidy instances start by executing `start_mopidy.sh`. This script performs the following actions:
   - Logs relevant information to the console for debugging and monitoring purposes.
   - Attempts to install Python packages listed in the `requirements.txt` file, with the file path specified in the `REQUIREMENTS_FILE` environment variable.
   - Triggers `start.py`, which serves several key functions:
     - It checks for and terminates any processes already running on the specified ports, ensuring a clean start.
     - Removes any streams in Snapcast with the same ID as the current instance to prevent conflicts.
     - Sends Snapcast information about the new stream, allowing synchronized audio playback.

5. **Mopidy Execution**: With all the necessary preparations complete, Mopidy starts running. Users can access it via the specified web port. Note that issues with Mopidy's configuration file (`mopidy.conf`) can lead to connectivity problems. Be cautious when modifying this file, as adding a `;` to a line renders the entire line invalid. Ensure that any changes made are properly configured to avoid disruptions in Mopidy's operation.

## Environment Variables

Here's a table describing the environment variables used in the Dockerfile and how they are utilized in the Python file:

| Environment Variable     | Description                                       | Usage in Python File                                                                                                 |
|--------------------------|---------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `XDG_CACHE_DIR`          | Cache directory path                              | Used to define the cache directory where Mopidy and other components can store cached data.                        |
| `XDG_CONFIG_DIR`         | Configuration directory path                      | Specifies the directory where Mopidy should look for its configuration file (`mopidy.conf`).                         |
| `XDG_DATA_DIR`           | Data directory path                               | Indicates the directory where Mopidy stores data, such as databases and other persistent information, except sometimes it just puts it in `/home/.local/share/mopidy` instead.               |
| `REQUIREMENTS_FILE`      | Requirements file path                            | Points to the location of the `requirements.txt` file, which is used for installing Python dependencies.              |
| `IRIS_USE_SUDO`          | Boolean flag (true or false)                     | Determines whether Mopidy Iris should use sudo when executing certain commands (typically set to `false`).         |
| `TEMPLATES_DIR`          | Templates directory path                         | Specifies the directory where various templates, including `mopidy.conf`, are stored for configuration purposes.     |

These environment variables are utilized in the Python file to configure and customize the behavior of the Mopidy and related services. They are used for various purposes such as defining file paths, configuring Mopidy, and specifying options for different components.
