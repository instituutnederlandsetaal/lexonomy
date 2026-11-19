import json
import os
from pathlib import Path


API_DIR = Path(__file__).resolve().parent


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


def load_siteconfig():
    with SITECONFIG_PATH.open(encoding="utf-8") as config_file:
        config = json.load(config_file)
    config["dataDir"] = str((API_DIR / config["dataDir"]).resolve())
    return config
