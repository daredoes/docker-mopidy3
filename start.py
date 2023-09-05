#!/bin/python3
import os
import json
import configparser
import requests
import signal
import hashlib
import typer
import subprocess

def kill_process_on_port(port):
    try:
        # Get the process ID (PID) associated with the specified port
        cmd = f'lsof -t -i:{port}'
        pid = subprocess.check_output(cmd.split()).decode().strip()

        # Terminate the process with the specified PID
        cmd = f'kill {pid}'
        print(f'Killing {pid} for port {port}')
        subprocess.call(cmd.split())
    except:
        print(f'No process that can be killed running on port {port}')

app = typer.Typer()

XDG_CONFIG_DIR = os.environ.get('XDG_CONFIG_DIR', '/etc/mopidy')
TEMPLATES_DIR = os.environ.get('TEMPLATES_DIR', '/home/templates')

CONFIG_PATH = f"{XDG_CONFIG_DIR}/mopidy.conf"
SERVER_CONFIG_PATH = f"{XDG_CONFIG_DIR}/settings.json"
SUPERVISORD_PATH = "/etc/supervisord.conf"

TEMPLATE_MOPIDY_PATH = f"{TEMPLATES_DIR}/mopidy.conf"
TEMPLATE_SUPERVISORD_MOPIDY_PATH = f"{TEMPLATES_DIR}/supervisord-mopidy.conf"
TEMPLATE_SUPERVISORD_PATH = f"{TEMPLATES_DIR}/supervisord.conf"


def string_to_hex(string: str):
    """Converts a string into a hexadecimal digest so that the characters are safe"""
    return hashlib.sha1(str(string).encode("utf-8")).hexdigest()


def write_file_contents(filepath: str, contents: str):
    """Opens a filepath and overwrites the contents"""
    with open(filepath, "w") as f:
        f.write(contents)


def read_file_contents(filepath: str):
    """Opens a filepath and reads the contents"""
    with open(filepath, "r") as f:
        return f.read()


def write_supervisord_conf(contents: str):
    """Writes content to the SUPERVISORD main configuration file"""
    write_file_contents(SUPERVISORD_PATH, contents)

def get_stream_id(stream_id: str = ""):
    return stream_id if stream_id else os.environ.get("STREAM_ID")

def stream_id_to_hex(stream_id: str = ""):
    hex = string_to_hex(get_stream_id(stream_id))
    return hex

def get_mopidy_config_path(stream_id: str = ""):
    hex = stream_id_to_hex(get_stream_id(stream_id))
    path = f"{XDG_CONFIG_DIR}/mopidy{hex}.conf"
    return path


def write_mopidy_config(modified_config: configparser.ConfigParser):
    """Writes a mopidy config to """
    path = get_mopidy_config_path()
    with open(path, 'w') as f:
        modified_config.write(f)
        print(f"Mopidy config written to {path}")
    return path


def modify_mopidy_conf(
    config, mpd=None, http=None, port=4953
):
    modified_config = configparser.ConfigParser() # create empty config
    # Read given, or pull from default
    if os.path.exists(config):
        print(f"Modifying config from {config}")
        modified_config.read(config)
    else:
        print(f"Modifying config from {TEMPLATE_MOPIDY_PATH}")
        with open(TEMPLATE_MOPIDY_PATH, "r") as f:
            modified_config.read_file(f)
    if mpd:
        try:
            modified_config["mpd"]["port"] = mpd
            print(f"modified mpd with port {mpd}")
        except KeyError:
            print(f"unable to modify mpd with port {mpd}")
    if http:
        try:
            modified_config["http"]["port"] = http
            print(f"modified http with port {http}")
        except KeyError:
            print(f"unable to modify http with port {http}")
    # Turns out this is deprecated
    # if modified_config["iris"]:
    #     if name:
    #         print(f"modified iris with stream {name}")
    #         modified_config["iris"]["snapcast_stream"] = name
    #     if snapcast:
    #         if snapcast.get("enabled", False):
    #             snapcast_enabled = "true" if snapcast.get("enable_in_iris", True) else "false"
    #             print(f"modified iris with snapcast_enabled is {snapcast_enabled}")
    #             modified_config["iris"]["snapcast_enabled"] = snapcast_enabled
    #         host = snapcast.get("host", None)
    #         port = snapcast.get("port", None)
    #         ssl = snapcast.get("use_ssl", None)
    #         if host:
    #             modified_config["iris"]["snapcast_host"] = host
    #             print(f"modified iris with host {host}")
    #         if port:
    #             modified_config["iris"]["snapcast_port"] = f'{port}'
    #             print(f"modified iris with port {port}")
    #         if ssl:
    #             modified_config["iris"]["snapcast_ssl"] = "true" if ssl else "false"
    #             print(f"modified iris with ssl {ssl}")
    if port:
        try:
            modified_config["audio"]["output"] = modified_config["audio"]["output"].replace(
                "port=4953", f"port={port}"
            )
            print(f"modified snapfifo with port {port}")
        except KeyError:
            print(f"unable to modify snapfifo with port {port}")
    # Returns filepath of new config
    return write_mopidy_config(modified_config)


def remove_stream_from_snapcast(
    id=None, server_ip="localhost", port=1780, ssl=False, **kwargs
):
    id = get_stream_id(id)
    try:
        payload = {
            "id": 8,
            "jsonrpc": "2.0",
            "method": "Stream.RemoveStream",
            "params": {"id": id},
        }
        url = (
            f'http{"s" if ssl else ""}://{server_ip}{f":{port}" if port else ""}/jsonrpc'
        )
        response = requests.post(
            url=url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        if response.status_code == 200:
            response_json = response.json()
            print(f"Cleared stream: {id}")
            return response_json
    except Exception:
        return {}


def add_stream_to_snapcast(
    name, tcp_port=4953, server_ip="localhost", port=1780, ssl=False, client_ip="0.0.0.0", **kwargs
):
    remove_stream_from_snapcast(name, server_ip=server_ip, port=port, ssl=ssl)
    try:
        sample_format = os.environ.get("SNAPCAST_SAMPLEFORMAT", "44100:16:2")
        params = os.environ.get("SNAPCAST_STREAM_PARAMS", "&send_to_muted=false&controlscript=meta_mopidy.py")
        payload = {
            "id": 8,
            "jsonrpc": "2.0",
            "method": "Stream.AddStream",
            "params": {
                "streamUri": f"tcp://{client_ip}:{tcp_port}?name={name}&sampleformat={sample_format}&mode=client{params}"
            },
        }
        url = (
            f'http{"s" if ssl else ""}://{server_ip}{f":{port}" if port else ""}/jsonrpc'
        )
        response = requests.post(
            url=url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        print("Payload to snapcast", payload)
        if response.status_code == 200:
            response_json = response.json()
            print("Added stream to Snapcast", response_json)
            return response_json
        else:
            print("bad response", response)
    except Exception as e:
        print(e)
        return {}


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


# How to use Graceful Killer
# @app.command()
# def stop():
#     killer = GracefulKiller()
#     while not killer.kill_now:
#         time.sleep(1)
#         print("Waiting for cleanup process")

#     print("Do something here during clean up")


class SupervisordMopidyConfBuilder:
    config = configparser.ConfigParser(default_section=None)

    def __init__(self) -> None:
        filepath = TEMPLATE_SUPERVISORD_MOPIDY_PATH
        if os.path.exists(filepath):
            print(f'Loading supervisord mopidy config from "{filepath}')
            with open(filepath, "r") as f:
                self.config.read_file(f)

    def get_instance_config(self, stream_id: str, config_filepath: str, port: int = 4953):
        instance_config = {}
        hex = string_to_hex(get_stream_id(stream_id))
        try:
            for options in self.config.items("program"):
                option, value = options
                instance_config[option] = value
        except configparser.NoSectionError:
            pass
        if not instance_config.get("process_name"):
            instance_config["process_name"] = stream_id.replace(" ", "_")
        env_vars = instance_config.get("environment", "")
        split_vars = []
        if env_vars:
            split_vars.extend(env_vars.split(","))
        if "STREAM_ID" not in split_vars:
            split_vars.append(f'STREAM_ID="{stream_id}"')
        if "CONFIG_FILEPATH" not in split_vars:
            split_vars.append(f"CONFIG_FILEPATH={config_filepath}")
        if "TCP_PORT" not in split_vars:
            split_vars.append(f"TCP_PORT={port}")
        instance_config["environment"] = ",".join(split_vars)

        return {f"program:mopidy{hex}": instance_config}


class SupervisordConfBuilder:
    config = configparser.ConfigParser(default_section=None)

    def __init__(self) -> None:
        filepath = TEMPLATE_SUPERVISORD_PATH
        if os.path.exists(filepath):
            print(f'Loading supervisord config from "{filepath}')
            with open(filepath, "r") as f:
                self.config.read_file(f)

    def add_program(self, name: str, options: dict) -> None:
        try:
            self.config.add_section(name)
        except configparser.DuplicateSectionError:
            pass
        self.config[name] = options

    def remove_program(self, name: str) -> bool:
        return self.config.remove_section(name)

    def save(self) -> None:
        with open(SUPERVISORD_PATH, "w") as f:
            self.config.write(f)


def get_server_config_data() -> dict:
    data = {}
    if os.path.exists(SERVER_CONFIG_PATH):
        # Read file, and quickly close
        with open(SERVER_CONFIG_PATH, "r") as f:
            data = json.load(f)
    return data


@app.command()
def create_supervisord_conf():
    """This runs first"""
    supervisord_config_builder = SupervisordConfBuilder()
    supervisord_mopidy_config_builder = SupervisordMopidyConfBuilder()

    data = get_server_config_data()
    print(f"Got data", data)
    servers = data.get("servers", {})
    if servers:
        server_names = servers.keys()
        server_count = len(server_names)
        print(f"Writing {server_count} mopidy supervisord configs")
        for index, server_name in enumerate(server_names, start=1):
            mopidy_conf = get_mopidy_config_path(server_name)
            server_data = servers.get(server_name, {})
            print(f"Writing mopidy supervisord config {index}/{server_count}", server_data)
            tcp_port = server_data.get("tcp", 4953)
            mopidy_configs = supervisord_mopidy_config_builder.get_instance_config(
                server_name, mopidy_conf, tcp_port
            )
            for program_name, program_options in mopidy_configs.items():
                supervisord_config_builder.add_program(
                    program_name,
                    program_options,
                )
    else:
        print("Writing main mopidy supervisord config")
        server_name = os.environ.get("STREAM_ID", "Home")
        mopidy_conf = get_mopidy_config_path(server_name)
        mopidy_configs = supervisord_mopidy_config_builder.get_instance_config(
            server_name, mopidy_conf, 4953
        )
        for program_name, program_options in mopidy_configs.items():
            supervisord_config_builder.add_program(
                program_name,
                program_options,
            )
    supervisord_config_builder.save()


@app.command()
def cleanup(stream_id: str = ""):
    name = get_stream_id(stream_id)
    if name and os.path.exists(SERVER_CONFIG_PATH):
        with open(SERVER_CONFIG_PATH, "r") as f:
            data = json.load(f)
            snapcast = dict(data.get("snapcast", {}))
            if snapcast:
                print(f"Found snapcast settings\n{snapcast}")
                remove_stream_from_snapcast(name, **snapcast)


@app.command()
def create(stream_id: str = "", port: int = 4953):
    name = os.environ.get("STREAM_ID", stream_id)
    count = string_to_hex(name)
    if name:
        data = get_server_config_data()
        server_config = data.get("servers", {}).get(name, {})
        snapcast = server_config.get("snapcast", {})
        if server_config:
            mpd = str(server_config.get("mpd"))
            http = str(server_config.get("http"))
            if mpd:
                kill_process_on_port(mpd)
                kill_process_on_port(http)
            if mpd and http:
                config_filepath = modify_mopidy_conf(
                    CONFIG_PATH,
                    mpd=mpd,
                    http=http,
                    port=port
                )
                print(f"Wrote config to: {config_filepath}")
        if snapcast:
            print(f"Found snapcast settings")
            add_stream_to_snapcast(name, tcp_port=port, **snapcast)
    else:
        print(
            "Trying to create stream without name. Make sure STREAM_ID is set in the environment"
        )


if __name__ == "__main__":
    app()
