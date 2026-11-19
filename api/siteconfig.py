import json
import os
from pathlib import Path


API_DIR = Path(__file__).resolve().parent
SITECONFIG_PATH = API_DIR / (os.environ.get("LEXONOMY_SITECONFIG") or "siteconfig.json")


def load_siteconfig():
    with SITECONFIG_PATH.open(encoding="utf-8") as config_file:
        config = json.load(config_file)
    config["dataDir"] = str((API_DIR / config["dataDir"]).resolve())
    return config
