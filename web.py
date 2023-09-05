from aiohttp import web
from typing import Dict, cast
import json
import os
import pathlib
import hashlib

SETTINGS_DIR = os.environ.get("XDG_CONFIG_DIR", "/etc/mopidy")
SETTINGS_FILE = f"{SETTINGS_DIR}/settings.json"

def string_to_hex(string: str):
    """Converts a string into a hexadecimal digest so that the characters are safe"""
    return hashlib.sha1(str(string).encode("utf-8")).hexdigest()



class SnapcastServer:
    enabled: bool
    server_ip: str
    client_ip: str
    port: int
    ssl: bool

    def __init__(
        self,
        enabled=True,
        server_ip="0.0.0.0",
        client_ip="0.0.0.0",
        port=1780,
        ssl=False,
        **kwargs
    ) -> None:
        self.enabled = enabled
        self.server_ip = server_ip
        self.client_ip = client_ip
        self.port = port
        self.ssl = ssl


class MopidyServer:
    mpd: int
    http: int
    tcp: int
    snapcast: SnapcastServer

    def __init__(
        self, mpd=6600, http=6680, tcp=4953, snapcast: SnapcastServer = None, **kwargs
    ) -> None:
        self.mpd = mpd
        self.http = http
        self.tcp = tcp
        self.snapcast = snapcast if snapcast is not None else SnapcastServer()


class Settings:
    servers: Dict[str, MopidyServer]

    def __init__(self, servers: Dict[str, MopidyServer] = None) -> None:
        self.servers = servers if servers is not None else {"New Server": MopidyServer()}

    def to_json_str(self) -> str:
        return json.dumps({"servers": self.servers}, cls=SettingsEncoder, indent=4, sort_keys=True)

# subclass JSONEncoder
class SettingsEncoder(json.JSONEncoder):
        def default(self, o):
            return o.__dict__

file_path = pathlib.Path(os.path.realpath(__file__)).parent
routes = web.RouteTableDef()


tailwindJS = ""
with open("tailwind.js", 'r') as f:
    tailwindJS = f.read()

HOMEPAGE_START = f"""
    <html>
        <head>
        <script>
        {tailwindJS}
        </script>
        </head>
        <body class="flex flex-col gap-3 py-1 px-2">
"""
HOMEPAGE_END = """
        </body>
    </html>
"""

def make_form(name, *args: list, form_class='flex flex-col justify-start align-center gap-1', ):
    header = f"<h3 class='text-3xl font-bold'>{name}</h3>" if name else ""
    inputs = ""
    for arg in args:
        inputs += str(arg)
    return f"""
        {header}
        <form class="{form_class}" method="post">
        {inputs}
        <button class="border border-solid" type="submit">Submit</button>
        </form>
    """

def make_input(name, value=None, placeholder=None, input_type="text", children="", show_label=False, label=None, props="", checked=False):
    final_html = ""
    input_html = f"<input {'checked' if checked else ''} class='border border-solid' type='{input_type}' placeholder='{placeholder}' name='{name}' value='{value}' {props}>{children}</input>"
    if show_label:
        final_html = f"<div class='flex flex-row justify-start align-center gap-2'><label class='capitalize' for='{name}'>{label if label else name}</label>{input_html}</div>"
    else:
        final_html = input_html
    return final_html


def make_page(content):
    return f"""
    {HOMEPAGE_START}
    {content}
    {HOMEPAGE_END}
    """


def save_app_to_settings(app: web.Application) -> bool:
    try:
        settings = app["settings"]
        print("Saving Settings")
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, cls=SettingsEncoder, indent=4, sort_keys=True)
        return True
    except Exception as e:
        print(e)
        return False


class SettingsNotFoundException(Exception):
    pass


def load_settings() -> list:
    try:
        with open(SETTINGS_FILE, "r") as f:
            data: dict = json.load(f)
            loaded_servers = data.get("servers", {})
            servers = {}
            for server_name in loaded_servers.keys():
                server_data = loaded_servers[server_name]
                snapcast = server_data.pop("snapcast", {})
                servers[server_name] = MopidyServer(**server_data, snapcast=SnapcastServer(**snapcast))
            return Settings(servers=servers)
    except Exception as e:
        print(f"Failed to load settings from {SETTINGS_FILE}", e)
        raise (SettingsNotFoundException(e))


async def on_startup(app: web.Application) -> None:
    settings = Settings()
    try:
        settings = load_settings()
    except SettingsNotFoundException:
        pass
    app["settings"] = settings
    print("Loaded settings")


async def on_shutdown(app: web.Application) -> None:
    if save_app_to_settings(app):
        print(f"Saved settings to {SETTINGS_FILE}")
    else:
        print(f"Failed to save settings to {SETTINGS_FILE}")



def load_server(method):
    async def _handler(request: web.Request):
        server_id = request.match_info["id"]
        settings: Settings = request.app["settings"]
        server = settings.servers.get(server_id, None)
        if not server:
            server = MopidyServer()
        return await method(request, server_id, server)

    return _handler

def alter_settings(method):
    async def _handler(request: web.Request):
        server_id = request.match_info["id"]
        settings: Settings = request.app["settings"]
        server = settings.servers.get(server_id, None)
        if not server:
            return web.Response(text=f"No Server For {server_id}", status=500)
        result = await method(request, server_id, server)
        save_app_to_settings(request.app)
        return result

    return _handler

@routes.get("/")
async def homepage(request: web.Request):
    settings: Settings = request.app.get("settings", Settings())
    if settings.servers:
        serverNames = settings.servers.keys()
        output = "<h2 class='text-3xl font-bold'>Servers</h2><div class='flex flex-col gap-2'>"
        output += "".join(
            f"<a class='font-medium text-blue-600 dark:text-blue-500 hover:underline' href='{server_name}'>{index}: {server_name}</a>"
            for index, server_name in enumerate(serverNames, start=1)
        )
        count = 0
        while count >= 0:
            server_name = f"New Server{f' {count}' if count else ''}"
            if server_name in serverNames:
                count += 1
            else:
                output += f"<a class='font-medium text-blue-600 dark:text-blue-500 hover:underline' href='{server_name}'>{server_name}</a>"
                break
        output += "</div>"
    else:
        raise web.HTTPFound(location=f"/New Server")
    return web.Response(text=make_page(output), content_type="text/html")


@routes.get("/{id}")
@load_server
async def server_settings(request, server_name, server: MopidyServer):
    is_checked = 'checked="true"'
    snapcast_inputs = [
        make_input("snapcastEnabled", "true", input_type='checkbox', label="Enabled", show_label=True, checked=server.snapcast.enabled),
        make_input("snapcastServerIp", server.snapcast.server_ip, label="Server IP Address", show_label=True),
        make_input("snapcastClientIp", server.snapcast.client_ip, label="Client IP Address (usually 0.0.0.0)", show_label=True),
        make_input("snapcastPort", server.snapcast.port, input_type='number', props="max='25565' min='0'", label="Server Port", show_label=True),
        make_input("snapcastSSL", "true", input_type='checkbox', label="Use SSL?", show_label=True, checked=server.snapcast.ssl),
    ]
    inputs = [
        make_input("name", server_name, "Server Name", show_label=True),
        make_input("mpd", server.mpd, "MPD Port", show_label=True, input_type="number"),
        make_input("http", server.http, "HTTP Port", show_label=True, input_type="number"),
        make_input("tcp", server.tcp, "TCP Port", show_label=True, input_type="number"),
        f"<h5 class='text-xl font-extrabold'>Snapcast Settings</h5><div class='px-2 flex flex-col justify-start align-center gap-2'>{''.join(snapcast_inputs)}</div>"
    ]
    output = make_form(f"{server_name} Settings", *inputs)
    output += "<div><p>Restart the container for setting changes to take effect.</p></div>"
    return web.Response(text=make_page(output), content_type="text/html")

@routes.post("/{id}")
@alter_settings
async def save_server_settings(request: web.Request, server_name: str, *args, **kwargs):
    data = await request.post()
    server_id = server_name
    if server_id:
        print("Got Server ID", server_id)
        oldSettings = cast(Settings, request.app["settings"])
        oldServer = oldSettings.servers.get(server_id, None)
        if oldServer:
            print("Found server data", data)
            newName = data.get('name', None)
            newMpd = data.get('mpd', None)
            newHttp = data.get('http', None)
            newTcp = data.get('tcp', None)
            snapcastEnabled = True if data.get('snapcastEnabled', None) == "true" else False
            snapcastServerIp = data.get('snapcastServerIp', None)
            snapcastClientIp = data.get('snapcastClientIp', None)
            snapcastPort = data.get('snapcastPort', None)
            snapcastSSL = True if data.get('snapcastSSL', None) == "true" else False
            oldServer.mpd = newMpd
            oldServer.http = newHttp
            oldServer.tcp = newTcp
            oldServer.snapcast.enabled = snapcastEnabled
            oldServer.snapcast.server_ip = snapcastServerIp
            oldServer.snapcast.client_ip = snapcastClientIp
            oldServer.snapcast.port = snapcastPort
            oldServer.snapcast.ssl = snapcastSSL
            if not newName or server_id == newName:
                newName = server_id
            else:
                del oldSettings.servers[server_id]
                oldSettings.servers[newName] = oldServer
            request.app["settings"] = oldSettings
            raise web.HTTPFound(location=f"/{newName}")
    return {}

def main():
    app = web.Application()
    print("loading app")
    app["settings"] = {}
    print("adding routes")
    app.add_routes(routes)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, host="0.0.0.0", port=os.environ.get("PORT", 731))


if __name__ == "__main__":
    print("starting web server")
    main()
