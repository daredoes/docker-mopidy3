#!/bin/python3
import os
import re
import json
import configparser

program_template_string =  """
[program:{name}]
directory=/tmp
environment = PYTHONUNBUFFERED=1
command=/usr/bin/mopidy {options}
"""

SUPERVISORD_CONF = """
[supervisord]
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
nodaemon=true

[inet_http_server]
port = 0.0.0.0:9001

"""

CONFIG_PATH = '/config/mopidy.conf'
SERVER_CONFIG_PATH = '/config/servers.json'
SUPERVISORD_PATH = '/etc/supervisord.conf'

def write_supervisord_conf(contents):
    with open(SUPERVISORD_PATH, 'w') as f:
        f.write(contents)

def write_mopidy_config(modified_config, count=''):
    path = f'/tmp/mopidy{count}.conf'
    with open(path, 'w') as f:
        modified_config.write(f)
    print(f'Mopidy config written to {path}')
    return path


def sub_group_in_regex(regex, substitute, config):
    result = re.sub(regex, substitute, config)
    return str(result)

def modify_mopidy_conf(config, mpd=None, http=None, count=''):
    snapfifo = f'/tmp/snapfifo{count}'
    modified_config = configparser.ConfigParser()
    modified_config.read(config)
    if mpd:
        print(f'modify mpd with port {mpd}')
        modified_config['mpd']['port'] = mpd
    if http:
        print(f'modify http with port {http}')
        modified_config['http']['port'] = http
    if snapfifo:
        print(f'modify snapfifo with folder {snapfifo}')
        modified_config['audio']['output'] = modified_config['audio']['output'].replace('/tmp/snapfifo', snapfifo)
    return write_mopidy_config(modified_config, count)

def build_program_config(name, mopidy_config, mpd=None, http=None, count=''):
    options = ""
    config_filepath = modify_mopidy_conf(mopidy_config, mpd=mpd, http=http, count=count)
    if (os.path.exists(config_filepath)):
        options += f"--config {config_filepath}"
    command = program_template_string.format(name=name, options=options)
    return command

def main():
    mopidy_config = ""
    if (os.path.exists(CONFIG_PATH)):
        mopidy_config = CONFIG_PATH

    config = SUPERVISORD_CONF
    # Build Main Instance
    print('Writing main mopidy supervisord config')
    config += build_program_config('Mopidy Instance', mopidy_config)
    if (os.path.exists(SERVER_CONFIG_PATH)):
        with open(SERVER_CONFIG_PATH, 'r') as f:
            data = json.load(f)
            servers = data.get('servers', [])
            server_count = len(servers)
            print(f'Writing {server_count} extra mopidy supervisord configs')
            for index, server in enumerate(servers, start=1):
                print('Writing extra mopidy supervisord config {index}/{server_count}')
                mpd = str(server.get('mpd'))
                http = str(server.get('http'))
                config += build_program_config(f'Mopidy Instance {index}', mopidy_config, count=index, mpd=mpd, http=http)
    
    print('Writing supervisord config')
    write_supervisord_conf(config)

if __name__ == "__main__":
    main()