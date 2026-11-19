#!/usr/bin/env python3

import argparse
from contextlib import closing
import hashlib
from pathlib import Path
import secrets
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from siteconfig import load_siteconfig

parser = argparse.ArgumentParser(description="Reset the password for a Lexonomy account.")
parser.add_argument("email")
email = parser.parse_args().email

path = Path(load_siteconfig()["dataDir"]) / "lexonomy.sqlite"
password = secrets.token_urlsafe(18)
passhash = hashlib.sha1(password.encode("utf-8")).hexdigest()
try:
    with closing(sqlite3.connect(path.as_uri() + "?mode=rw", uri=True)) as conn, conn:
        result = conn.execute("UPDATE users SET passwordHash=? WHERE email=?", (passhash, email))
        if not result.rowcount:
            sys.exit(f"No Lexonomy account found for {email} in {path}")
except sqlite3.Error as e:
    sys.exit(f"Could not update the password for {email} in {path}: {e}")
print(f"User {email} now has a new password: {password}")
