import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


API_DIR = Path(__file__).resolve().parent
DEFAULT_PORT = 8000
_JSONC_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|(?P<comment>//[^\r\n]*|/\*[\s\S]*?\*/)')


def find_siteconfig():
    override = os.environ.get("LEXONOMY_SITECONFIG")
    if override:
        return API_DIR / override

    root = API_DIR.parent
    for path in (
        root / "config" / "siteconfig.json",
        API_DIR / os.environ.get("LEXONOMY_SITECONFIG_FALLBACK", "siteconfig.json"),
        root / "siteconfig.example.json",
    ):
        if path.exists():
            return path
    return root / "config" / "siteconfig.example.json"


SITECONFIG_PATH = find_siteconfig()


def parse_site_url(value, default_host):
    value = value.strip() or "/"
    path_only = value.startswith("/")
    has_scheme = "://" in value
    url = urlsplit(value if has_scheme or path_only else "//" + value)
    path = url.path.rstrip("/") + "/"
    if (url.scheme not in ("", "http", "https") or url.username is not None
            or "?" in value or "#" in value or value.startswith("//")
            or (not path_only and not url.hostname)
            or not re.fullmatch(r"(?:/[\w.~-]+)*/", path, re.ASCII)
            or any(part in (".", "..") for part in path.split("/"))):
        raise ValueError(f"Invalid Lexonomy URL: {value!r}")
    port = url.port
    if port == 0:
        raise ValueError("Lexonomy URL port must be positive")
    if port is None and not has_scheme:
        port = DEFAULT_PORT
    return url.scheme or "http", url.hostname or default_host, port, path


def read_siteconfig(path):
    # Match strings whole and replace comments with whitespace to preserve JSON error positions.
    def replace_comment(match):
        return re.sub(r"[^\r\n]", " ", match[0]) if match["comment"] else match[0]

    return json.loads(_JSONC_TOKEN.sub(replace_comment, path.read_text(encoding="utf-8")))


def parse_http_origin(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"http://(?:[a-z0-9._-]+|\[[0-9a-f:.]+\])(?::[0-9]+)?", value, re.IGNORECASE | re.ASCII
    ):
        raise ValueError(f"Expected an HTTP origin such as http://lexonomy.home:8000, got {value!r}")
    url = urlsplit(value)
    port = url.port
    if port == 0:
        raise ValueError("HTTP origin port must be positive")
    return url.hostname, port or 80


def load_siteconfig():
    config = read_siteconfig(SITECONFIG_PATH)
    config["dataDir"] = str((API_DIR / config["dataDir"]).resolve())
    # Older config files used separate route and port settings.
    server_url = config.get("serverUrl", config.get("rootPath", "/"))
    _, host, port, path = parse_site_url(server_url, "0.0.0.0")
    if "serverUrl" not in config and (config.get("port") or 0) > 0:
        port = config["port"]
    port = port or DEFAULT_PORT
    config["serverAddress"] = (host, port, path)

    client_url = config.get("clientUrl", config.get("baseUrl", ""))
    if client_url.strip():
        scheme, host, port, path = parse_site_url(client_url, "localhost")
    else:
        scheme = "http"
        if host == "0.0.0.0":
            host = "localhost"
    authority = f"[{host}]" if ":" in host else host
    if port not in (None, 80):
        authority += f":{port}"
    config["clientUrl"] = f"{scheme}://{authority}{path}"

    api_url = config.get("apiUrl", "").strip()
    if api_url:
        if not api_url.startswith("/") and "://" not in api_url:
            raise ValueError("apiUrl must be an HTTP(S) URL or a path starting with '/'")
        _, _, _, api_path = parse_site_url(api_url, "localhost")
        config["apiUrl"] = urlsplit(api_url)._replace(path=api_path).geturl()
    else:
        config["apiUrl"] = config["clientUrl"]

    http_login_origins = config.get("allowHttpLoginOn", [])
    if not isinstance(http_login_origins, list):
        raise ValueError("allowHttpLoginOn must be an array of HTTP origins")
    config["allowHttpLoginOn"] = {parse_http_origin(origin) for origin in http_login_origins}
    return config
