#!/bin/python3
import os
import re
import json
import configparser
import requests
import signal
import time
import logging
import typer

app = typer.Typer()

program_template_string = """
[program:{name}]
directory=/tmp
process_name={process_name}
environment = PYTHONUNBUFFERED=1
redirect_stderr=true
killasgroup=true
stopasgroup=true
command=/usr/bin/mopidy {options}
"""

SUPERVISORD_CONF = """
[supervisord]
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
nodaemon=true

[inet_http_server]
port = 0.0.0.0:9001

[program:cleanup]
directory=/tmp
command=/bin/python3 /start.py stop


"""

DEFAULT_MOPIDY_CONFIG = """
[core]
cache_dir = $XDG_CACHE_DIR/mopidy
config_dir = $XDG_CONFIG_DIR/mopidy
data_dir = $XDG_DATA_DIR/mopidy
max_tracklist_length = 10000
restore_state = false

[logging]
verbosity = 1
format = %(levelname)-8s %(asctime)s [%(process)d:%(threadName)s] %(name)s\n  %(message)s
color = true
config_file =

[audio]
mixer = software
mixer_volume = 
output = tee name=t ! queue ! audioresample ! audioconvert ! audio/x-raw,rate=48000,channels=2,format=S16LE ! filesink location=/tmp/snapfifo t. 
buffer_time = 

[youtube]
enabled = true
allow_cache = 
youtube_api_key = 
search_results = 15
playlist_max_videos = 20
api_enabled = false
channel_id = 
musicapi_enabled = false
musicapi_cookie = 
autoplay_enabled = false
strict_autoplay = false
max_autoplay_length = 600
max_degrees_of_separation = 3
youtube_dl_package = youtube_dl

[tunein]
enabled = false
timeout = 5000
filter = 

[podcast]
enabled = false
browse_root = Podcasts.opml
browse_order = desc
lookup_order = asc
cache_size = 64
cache_ttl = 86400
timeout = 10

[podcast-itunes]
enabled = false
base_url = http://itunes.apple.com/
country = US
explicit = 
charts = audioPodcasts
charts_limit = 20
search_limit = 20
timeout = 10
retries = 3

[musicbox_webclient]
enabled = false
musicbox = false
websocket_host = 
websocket_port = 
on_track_click = PLAY_ALL

[muse]
enabled = true
mopidy_host = 
mopidy_port = 
mopidy_ssl = false
snapcast_host = 
snapcast_port = 
snapcast_ssl = false

[mpd]
enabled = true
hostname = 0.0.0.0
port = 6600
password = 
max_connections = 20
connection_timeout = 60
default_playlist_scheme = m3u

[mobile]
enabled = false
title = Mopidy Mobile on $hostname
ws_url = 

[local-images]
enabled = true
library = json
base_uri = /images/
image_dir = 
album_art_files = 
  *.jpg
  *.jpeg
  *.png

[iris]
enabled = true
country = US
locale = en_US
verify_certificates = true
snapcast_enabled = false
snapcast_host = 
snapcast_port = 
snapcast_ssl = 
snapcast_stream = Iris
spotify_authorization_url = https://jamesbarnsley.co.nz/iris/auth_spotify.php
lastfm_authorization_url = https://jamesbarnsley.co.nz/iris/auth_lastfm.php
genius_authorization_url = https://jamesbarnsley.co.nz/iris/auth_genius.php
data_dir = $XDG_DATA_DIR/iris

[file]
enabled = true
media_dirs = 
  $XDG_MUSIC_DIR|Music
  ~/|Home
excluded_file_extensions = 
  .directory
  .html
  .jpeg
  .jpg
  .log
  .nfo
  .pdf
  .png
  .txt
  .zip
show_dotfiles = false
follow_symlinks = false
metadata_timeout = 1000

[http]
enabled = true
hostname = 0.0.0.0
port = 6680
allowed_origins = 
csrf_protection = true
default_app = mopidy

[m3u]
enabled = true
base_dir =
default_encoding = latin-1
default_extension = .m3u8
playlists_dir =

[softwaremixer]
enabled = true

[stream]
enabled = true
protocols = 
  http
  https
  mms
  rtmp
  rtmps
  rtsp
metadata_blacklist = 
timeout = 5000


[soundcloud]
enabled = false  ; Extension disabled due to config errors.
explore_songs = 25
auth_token =   ; Must be set.

[local]
enabled = true  ; Extension disabled due to config errors.
max_search_results = 100
media_dir = /media; Must be set.
scan_timeout = 1000
scan_flush_threshold = 100
scan_follow_symlinks = false
included_file_extensions = 
excluded_file_extensions = 
  .cue
  .directory
  .html
  .jpeg
  .jpg
  .log
  .nfo
  .pdf
  .png
  .txt
  .zip
directories = 
  Albums                  local:directory?type=album
  Artists                 local:directory?type=artist
  Composers               local:directory?type=artist&role=composer
  Genres                  local:directory?type=genre
  Performers              local:directory?type=artist&role=performer
  Release Years           local:directory?type=date&format=%25Y
  Tracks                  local:directory?type=track
  Last Week's Updates     local:directory?max-age=604800
  Last Month's Updates    local:directory?max-age=2592000
timeout = 10
use_artist_sortname = false
album_art_files = 
  *.jpg
  *.jpeg
  *.png

"""

CONFIG_PATH = "/config/mopidy.conf"
SERVER_CONFIG_PATH = "/config/servers.json"
SUPERVISORD_PATH = "/etc/supervisord.conf"
STREAMS_PATH = "/etc/streams.csv"


def write_supervisord_conf(contents):
    with open(SUPERVISORD_PATH, "w") as f:
        f.write(contents)


def write_stream_ids_csv(contents):
    with open(STREAMS_PATH, "w") as f:
        f.write(contents)


def read_stream_ids_csv():
    if os.path.exists(STREAMS_PATH):
        with open(STREAMS_PATH, "r") as f:
            return f.read().split(",")
    return []


def write_mopidy_config(modified_config, count=""):
    path = f"/tmp/mopidy{count}.conf"
    with open(path, "w") as f:
        modified_config.write(f)
    print(f"Mopidy config written to {path}")
    return path


def sub_group_in_regex(regex, substitute, config):
    result = re.sub(regex, substitute, config)
    return str(result)


def modify_mopidy_conf(config, mpd=None, http=None, count=""):
    snapfifo = f"/tmp/snapfifo{count}"
    modified_config = configparser.ConfigParser()
    if os.path.exists(config):
        modified_config.read(config)
    else:
        modified_config.read_string(DEFAULT_MOPIDY_CONFIG)
    if mpd:
        print(f"modify mpd with port {mpd}")
        modified_config["mpd"]["port"] = mpd
    if http:
        print(f"modify http with port {http}")
        modified_config["http"]["port"] = http
    if snapfifo:
        print(f"modify snapfifo with folder {snapfifo}")
        modified_config["audio"]["output"] = modified_config["audio"]["output"].replace(
            "/tmp/snapfifo", snapfifo
        )
    return write_mopidy_config(modified_config, count)


def build_program_config(name, mopidy_config, mpd=None, http=None, count=""):
    options = ""
    config_filepath = modify_mopidy_conf(mopidy_config, mpd=mpd, http=http, count=count)
    if os.path.exists(config_filepath):
        options += f"--config {config_filepath}"
    command = program_template_string.format(
        name=f"mopidy{count}",
        options=options,
        process_name=f"{name}".replace(" ", "_").replace(":", "-"),
    )
    return command


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


def clear_saved_streams(snapcast):
    print("Reading streams")
    stream_ids = read_stream_ids_csv()
    print(f"Got streams: {stream_ids}")
    for stream_id in stream_ids:
        print(f"Clearing stream: {stream_id}")
        remove_stream_from_snapcast(stream_id, **snapcast)


def add_stream_to_snapcast(
    name, pipe="/tmp/snapfifo", host="localhost", port=1780, use_ssl=False, **kwargs
):
    remove_stream_from_snapcast(name, host=host, port=port, use_ssl=use_ssl)
    try:
        payload = {
            "id": 8,
            "jsonrpc": "2.0",
            "method": "Stream.AddStream",
            "params": {"streamUri": f"pipe://{pipe}?name={name}"},
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
            return response_json
    except Exception:
        return {}


MAIN_SERVER_NAME = "Home"


def clear_saved_streams_from_file():
    if os.path.exists(SERVER_CONFIG_PATH):
        with open(SERVER_CONFIG_PATH, "r") as f:
            data = json.load(f)
            snapcast = dict(data.get("snapcast", {}))
            print(f"Found snapcast settings\n{snapcast}")
            clear_saved_streams(snapcast)


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


@app.command()
def stop():
    killer = GracefulKiller()
    while not killer.kill_now:
        time.sleep(1)
        logging.info("Waiting for cleanup process")

    logging.info("Attempting to clean up snapcast streams")
    clear_saved_streams_from_file()


@app.command()
def start():
    mopidy_config = ""
    if os.path.exists(CONFIG_PATH):
        mopidy_config = CONFIG_PATH

    config = SUPERVISORD_CONF
    # Build Main Instance

    stream_ids = []
    if os.path.exists(SERVER_CONFIG_PATH):
        with open(SERVER_CONFIG_PATH, "r") as f:
            data = json.load(f)
            servers = dict(data.get("servers", {}))
            snapcast = dict(data.get("snapcast", {}))
            server_count = len(servers.keys())
            print(f"Writing {server_count} extra mopidy supervisord configs")
            for index, server in enumerate(servers.items(), start=1):
                print("Writing extra mopidy supervisord config {index}/{server_count}")
                server_name, server_config = server
                mpd = str(server_config.get("mpd"))
                http = str(server_config.get("http"))
                if mpd and http:
                    config += build_program_config(
                        server_name, mopidy_config, count=index, mpd=mpd, http=http
                    )
                    if snapcast:
                        response = add_stream_to_snapcast(
                            server_name, pipe=f"/tmp/snapfifo{index}", **snapcast
                        )
                        stream_id = response.get("result", {}).get("id")
                        if stream_id:
                            print(f"Added stream id: {stream_id}")
                            stream_ids.append(stream_id)
    else:
        print("Writing main mopidy supervisord config")
        config += build_program_config(MAIN_SERVER_NAME, mopidy_config)

    if stream_ids:
        print("Writing stream ids csv")
        write_stream_ids_csv(",".join(stream_ids))

    print("Writing supervisord config")
    write_supervisord_conf(config)


if __name__ == "__main__":
    app()
