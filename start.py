#!/bin/python3
import os
import json
import configparser
import requests
import signal
import hashlib
import typer

app = typer.Typer()

CONFIG_PATH = "/config/mopidy.conf"
SERVER_CONFIG_PATH = "/config/servers.json"
SUPERVISORD_PATH = "/etc/supervisord.conf"
STREAMS_PATH = "/etc/streams.csv"

TEMPLATE_MOPIDY_PATH = "/home/templates/mopidy.conf"
TEMPLATE_SUPERVISORD_MOPIDY_PATH = "/home/templates/supervisord-mopidy.conf"
TEMPLATE_SUPERVISORD_PATH = "/home/templates/supervisord.conf"


def string_to_hex(string):
    return hashlib.sha1(str(string).encode("utf-8")).hexdigest()


def write_file_contents(filepath, contents):
    with open(filepath, "w") as f:
        f.write(contents)


def read_file_contents(filepath):
    with open(filepath, "r") as f:
        return f.read()


def write_supervisord_conf(contents):
    write_file_contents(SUPERVISORD_PATH, contents)


def write_mopidy_config(modified_config, count=""):
    path = f"/tmp/mopidy{count}.conf"
    with open(path, "w") as f:
        modified_config.write(f)
    print(f"Mopidy config written to {path}")
    return path


def modify_mopidy_conf(
    config, mpd=None, http=None, count="", name="", snapcast: dict = None
):
    snapfifo = f"/tmp/snapfifo{count}"
    modified_config = configparser.ConfigParser()
    if os.path.exists(config):
        modified_config.read(config)
    else:
        with open(TEMPLATE_MOPIDY_PATH, "r") as f:
            modified_config.read_file(f)
    if mpd:
        print(f"modified mpd with port {mpd}")
        modified_config["mpd"]["port"] = mpd
    if http:
        print(f"modified http with port {http}")
        modified_config["http"]["port"] = http
    if modified_config["iris"]:
        if name:
            print(f"modified iris with stream {name}")
            modified_config["iris"]["snapcast_stream"] = name
        if snapcast:
            if snapcast.get("enabled", False):
                snapcast_enabled = "true" if snapcast.get("enable_in_iris", True) else "false"
                print(f"modified iris with snapcast_enabled is {snapcast_enabled}")
                modified_config["iris"]["snapcast_enabled"] = snapcast_enabled
            host = snapcast.get("host", None)
            port = snapcast.get("port", None)
            ssl = snapcast.get("use_ssl", None)
            if host:
                modified_config["iris"]["snapcast_host"] = host
                print(f"modified iris with host {host}")
            if port:
                modified_config["iris"]["snapcast_port"] = f'{port}'
                print(f"modified iris with port {port}")
            if ssl:
                modified_config["iris"]["snapcast_ssl"] = "true" if ssl else "false"
                print(f"modified iris with ssl {ssl}")
    if snapfifo:
        print(f"modified snapfifo with folder {snapfifo}")
        modified_config["audio"]["output"] = modified_config["audio"]["output"].replace(
            "/tmp/snapfifo", snapfifo
        )
    # Returns filepath of new config
    return write_mopidy_config(modified_config, count)


def remove_stream_from_snapcast(
    id, host="localhost", port=1780, use_ssl=False, **kwargs
):
    try:
        payload = {
            "id": 8,
            "jsonrpc": "2.0",
            "method": "Stream.RemoveStream",
            "params": {"id": id},
        }
        url = (
            f'http{"s" if use_ssl else ""}://{host}{f":{port}" if port else ""}/jsonrpc'
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
    name, pipe="/data/snapfifo", host="localhost", port=1780, use_ssl=False, **kwargs
):
    remove_stream_from_snapcast(name, host=host, port=port, use_ssl=use_ssl)
    try:
        sample_format = os.environ.get("SNAPCAST_SAMPLEFORMAT", "44100:16:2")
        payload = {
            "id": 8,
            "jsonrpc": "2.0",
            "method": "Stream.AddStream",
            "params": {
                "streamUri": f"pipe://{pipe}?name={name}&sampleformat={sample_format}&send_to_muted=false&controlscript=meta_mopidy.py"
            },
        }
        url = (
            f'http{"s" if use_ssl else ""}://{host}{f":{port}" if port else ""}/jsonrpc'
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

    def get_instance_config(self, stream_id: str, config_filepath: str):
        instance_config = {}
        count = string_to_hex(stream_id)
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
        instance_config["environment"] = ",".join(split_vars)

        return {f"program:mopidy{count}": instance_config}


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
    supervisord_config_builder = SupervisordConfBuilder()
    supervisord_mopidy_config_builder = SupervisordMopidyConfBuilder()

    data = get_server_config_data()
    print(f"Got data", data)
    servers = data.get("servers", {})
    if servers:
        server_count = len(servers.keys())
        print(f"Writing {server_count} mopidy supervisord configs")
        for index, server_name in enumerate(servers.keys(), start=1):
            print(f"Writing mopidy supervisord config {index}/{server_count}")
            server_name
            mopidy_configs = supervisord_mopidy_config_builder.get_instance_config(
                server_name, f"/tmp/mopidy{string_to_hex(server_name)}.conf"
            )
            for program_name, program_options in mopidy_configs.items():
                supervisord_config_builder.add_program(
                    program_name,
                    program_options,
                )
    else:
        print("Writing main mopidy supervisord config")
        server_name = os.environ.get("STREAM_NAME", "Home")
        mopidy_configs = supervisord_mopidy_config_builder.get_instance_config(
            server_name, f"/tmp/mopidy.conf"
        )
        for program_name, program_options in mopidy_configs.items():
            supervisord_config_builder.add_program(
                program_name,
                program_options,
            )
    supervisord_config_builder.save()


@app.command()
def cleanup(stream_id: str = ""):
    name = os.environ.get("STREAM_ID", stream_id)
    if name and os.path.exists(SERVER_CONFIG_PATH):
        with open(SERVER_CONFIG_PATH, "r") as f:
            data = json.load(f)
            snapcast = dict(data.get("snapcast", {}))
            if snapcast:
                print(f"Found snapcast settings\n{snapcast}")
                remove_stream_from_snapcast(name, **snapcast)


@app.command()
def create(stream_id: str = ""):
    name = os.environ.get("STREAM_ID", stream_id)
    count = string_to_hex(name)
    if name:
        data = get_server_config_data()
        server_config = data.get("servers", {}).get(name, {})
        print(data)
        snapcast = data.get("snapcast", {})
        if server_config:
            mpd = str(server_config.get("mpd"))
            http = str(server_config.get("http"))
            if mpd and http:

                config_filepath = modify_mopidy_conf(
                    CONFIG_PATH,
                    mpd=mpd,
                    http=http,
                    count=count,
                    name=name,
                    snapcast=snapcast,
                )
                print(f"Wrote config to: {config_filepath}")
        if snapcast:
            print(f"Found snapcast settings")
            add_stream_to_snapcast(name, pipe=f"/data/snapfifo{count}", **snapcast)
    else:
        print(
            "Trying to create stream without name. Make sure STREAM_ID is set in the environment"
        )


if __name__ == "__main__":
    app()
