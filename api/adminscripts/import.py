#!/usr/bin/env python3

import os
import os.path
import atexit
import sqlite3
import sys
import datetime
import json
import argparse
import re
from xml.parsers.expat import ParserCreate
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops

parser = argparse.ArgumentParser(description='Import an xml file into a Lexonomy database.')
parser.add_argument("-p", "--purge", help="Purge dictionary before importing [default false]", dest="purge", action="store_true")
parser.add_argument("--no-purge", dest="purge", action="store_false")
parser.set_defaults(purge=False)
parser.add_argument("-pp", "--purge-history", help="Purge the dicationary, and also purge the history. This will speed up future operations. [default false]", dest="purge_history", action="store_true")
parser.add_argument("--no-purge-history", dest="purge_history", action="store_false")
parser.set_defaults(purge_history=False)
# Legacy import callers may pass these flags. The database stores entries only.
parser.add_argument("-a", "--save-all-content", help=argparse.SUPPRESS, dest="save_all_content", action="store_true")
parser.add_argument("--no-save-all-content", dest="save_all_content", action="store_false")
parser.set_defaults(save_all_content=False)
parser.add_argument("-u", "--user", help="Email of author (lexonomy account)", default="IMPORT@LEXONOMY")
parser.add_argument("--remove-upload", action="store_true", help="Remove the temporary upload after importing.")
parser.add_argument("database", help="Path to dictionary.sqlite, this should already exist.")
parser.add_argument("file", help="Path to file_to_import.xml")
args = parser.parse_args()

if args.remove_upload:
    atexit.register(Path(args.file).unlink, missing_ok=True)

print("PID "+ str(os.getpid()), flush=True)
print("Import started. Please wait...", flush=True)

dictID = os.path.basename(args.database).replace(".sqlite", "")
db = sqlite3.connect(args.database, )
db.row_factory = sqlite3.Row
db.isolation_level=None
db.execute("PRAGMA cache_size = -100000") # about 100 megs
db.execute("begin immediate")

historiography: dict[str, str] = {
    "importStart": str(datetime.datetime.now(datetime.timezone.utc)),
    "filename": os.path.basename(args.file)
}

if args.purge or args.purge_history:
    if args.purge_history: 
        print("Purging history...", flush=True)
        db.execute("delete from history")
    else:
        print("Copying all entries to history...", flush=True)
        db.execute("insert into history(entry_id, action, [when], email, xml, historiography) select id, 'purge', ?, ?, xml, ? from entries", (str(datetime.datetime.utcnow()), args.user, json.dumps(historiography)))

    # first delete from all related tables before deleting entries themselves - immense speadup due to faster constraint checking.
    print("Purging entries...", flush=True)
    db.execute("delete from sub")
    db.execute("delete from searchables")
    db.execute("delete from linkables")
    db.execute("delete from entries")

def import_entries(data: bytes, entry_tag: str) -> int:
    parser = ParserCreate("utf-8")
    opening_tag = re.compile(rb"""<[^"'<>]*(?:(?:"[^"]*"|'[^']*')[^"'<>]*)*>""")
    depth = 0
    entry_start = 0
    entry_depth = None
    entry_is_empty = False
    imported = 0

    def start_element(name, attrs):
        nonlocal depth, entry_tag, entry_start, entry_depth, entry_is_empty
        depth += 1
        if not entry_tag and depth == 2:
            entry_tag = name
        if name == entry_tag and entry_depth is None:
            entry_start = parser.CurrentByteIndex
            entry_depth = depth
            opening = opening_tag.match(data, entry_start)
            if not opening:
                raise ValueError("An entry must start with an XML opening tag.")
            entry_is_empty = data[opening.end() - 2:opening.end()] == b"/>"

    def end_element(name):
        nonlocal depth, entry_depth, imported
        if depth == entry_depth:
            end = parser.CurrentByteIndex
            # Expat points past an empty tag and at the start of an explicit closing tag.
            if not entry_is_empty:
                end = data.index(b">", end) + 1
            xml = data[entry_start:end].decode("utf-8")
            _, _, success, _ = ops.createEntry(db, configs, xml, args.user, commit=False)
            if not success:
                raise ValueError("An entry could not be imported.")
            imported += 1
            if imported % 100 == 0:
                percent = min(99, end * 100 // len(data))
                print(f"{percent}% - {imported} entries imported so far...", flush=True)
            entry_depth = None
        depth -= 1

    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.Parse(data, True)
    return imported


configs = ops.readDictConfigs(db)
xema = configs["xema"]
entry_tag = ops.xema_get_element_name_from_id(xema, xema["root"]) if xema.get("root") else ""
entries_imported = import_entries(Path(args.file).read_bytes(), entry_tag)
if not entries_imported:
    raise ValueError("The XML file contains no matching entries. The existing dictionary was kept.")

db.commit()
db.close()
print(f"100% - {entries_imported} total entries imported.", flush=True)
