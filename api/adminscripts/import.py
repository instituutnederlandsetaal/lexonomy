#!/usr/bin/env python3

import argparse
import atexit
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
from xml.parsers.expat import ExpatError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ops
from dictionary_document import prepare_dictionary


def main():
    parser = argparse.ArgumentParser(description="Import an XML document into a Lexonomy dictionary.")
    parser.add_argument("-p", "--purge", action=argparse.BooleanOptionalAction, default=False,
                        help="Replace entries and document layout. Keep history.")
    parser.add_argument("-pp", "--purge-history", action=argparse.BooleanOptionalAction, default=False,
                        help="Replace entries and document layout and delete history.")
    parser.add_argument("-u", "--user", default="IMPORT@LEXONOMY", help="Email of the author.")
    parser.add_argument("--remove-upload", action="store_true", help="Remove the temporary file after importing.")
    parser.add_argument("database", type=Path, help="Path to an existing dictionary database.")
    parser.add_argument("file", type=Path, help="Path to the XML document.")
    args = parser.parse_args()

    if args.remove_upload:
        atexit.register(args.file.unlink, missing_ok=True)

    print(f"PID {os.getpid()}", flush=True)
    print("Import started. Please wait...", flush=True)
    data = args.file.read_bytes()

    def progress(count, end):
        print(f"{min(99, end * 100 // len(data))}% - {count} entries imported so far...", flush=True)

    with closing(sqlite3.connect(args.database.resolve().as_uri() + "?mode=rw", uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=on")
        prepare_dictionary(db)
        try:
            count = ops.import_dictionary(db, data, args.user, progress, purge_entries=args.purge,
                                          purge_history=args.purge_history, filename=args.file.name)
        except (ExpatError, ValueError) as error:
            parser.exit(1, f"{error}\n")
    print(f"100% - {count} total entries imported.", flush=True)


if __name__ == "__main__":
    main()
