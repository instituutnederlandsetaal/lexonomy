#!/usr/bin/env python3

# Script to upgrade the schema of Lexonomy's main database.

from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from siteconfig import load_siteconfig

path = Path(load_siteconfig()["dataDir"]) / "lexonomy.sqlite"
print("Updating lexonomy database: %s" % path)
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row

#### HELPER FUNCTIONS ####

def get_table_column_names(conn, table):
    r = conn.execute("PRAGMA table_info(%s)" % table)
    return set([x[1] for x in r.fetchall()])

def do_query(conn, q):
    try:
        conn.execute(q)
    except sqlite3.Error as e:
        print("Database error: %s" % e)
        print("Query was: '%s'" % q)

#### ADDING NEW TABLES ####

do_query(conn, "CREATE TABLE IF NOT EXISTS recovery_tokens (email text, requestAddress text, token text, expiration datetime, usedDate datetime, usedAddress text)")
do_query(conn, "CREATE TABLE IF NOT EXISTS register_tokens (email text, requestAddress text, token text, expiration datetime, usedDate datetime, usedAddress text)")
do_query(conn, "CREATE TABLE IF NOT EXISTS dict_fav (dict_id text, user_email text)")
do_query(conn, "CREATE INDEX IF NOT EXISTS fav_dict_id on dict_fav (dict_id)")
do_query(conn, "CREATE INDEX IF NOT EXISTS fav_user_email on dict_fav (user_email)")

#### ADDING COLUMNS TO EXISTING TABLES ####

upgrades = {
    "users" : [("consent", "INTEGER")],
    "dicts" : [("language", "TEXT")]
}

for db, newcols in upgrades.items():
    db_columns = get_table_column_names(conn, db)
    for column in newcols:
        if column[0] not in db_columns:
            do_query(conn, "ALTER TABLE %s ADD COLUMN %s %s" % (db, column[0], column[1]))

#### COMMIT & DONE ####

conn.commit()
conn.close()
