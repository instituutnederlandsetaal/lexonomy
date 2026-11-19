#!/usr/bin/env python3

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3

from setup_admin import INITIAL_ADMIN, prepare_admin_setup

website = Path(__file__).resolve().parents[1]
config = json.loads(Path(os.environ.get("LEXONOMY_SITECONFIG", website / "siteconfig.json")).read_text(encoding="utf-8"))
data_dir = website / config["dataDir"]
data_dir.mkdir(parents=True, exist_ok=True)

for filename, setting, required in (
    ("lexonomy.sqlite", "dbSchemaFile", {"dicts", "users", "user_dict"}),
    ("crossref.sqlite", "dbXrefSchemaFile", {"links"}),
):
    with closing(sqlite3.connect(data_dir / filename)) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if not required <= tables:
            schema = (website / config[setting]).read_text(encoding="utf-8")
            conn.executescript("BEGIN IMMEDIATE;\n" + schema + "\nCOMMIT;")
            for table in required:
                conn.execute(f"SELECT 1 FROM {table} LIMIT 0")

with closing(sqlite3.connect(data_dir / "lexonomy.sqlite")) as conn:
    with conn:
        for email in config["admins"]:
            if email == INITIAL_ADMIN:
                continue
            password = secrets.token_urlsafe(18)
            result = conn.execute("INSERT INTO users (email, passwordHash) VALUES (?, ?) ON CONFLICT(email) DO NOTHING",
                                  (email, hashlib.sha1(password.encode()).hexdigest()))
            if result.rowcount:
                print(f"Created administrator {email}. Initial password: {password}")

    code = prepare_admin_setup(conn, config)
    if code:
        print(f"Lexonomy setup code for {INITIAL_ADMIN}: {code}", flush=True)
