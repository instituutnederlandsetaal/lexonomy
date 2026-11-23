"""The XML document around editable entries, stored as ordered markup and entry slots."""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from sqlite3 import Connection
from xml.parsers.expat import ParserCreate

from entryxml import ARCHIVE_PI, EMBEDDED, LXNM, SUBENTRY, rewrite

# A document consists of its prolog, ordered slots and the final root close and epilog.
# entry_id is nullable so removing an entry leaves its surrounding markup in place.
SCHEMA = """
CREATE TABLE IF NOT EXISTS document_parts (
    position INTEGER PRIMARY KEY,
    markup TEXT NOT NULL,
    is_slot BOOLEAN NOT NULL DEFAULT 0,
    entry_id INTEGER REFERENCES entries(id) ON DELETE SET NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS document_entry ON document_parts(entry_id) WHERE entry_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS searchables_by_entry ON searchables(entry_id);
CREATE INDEX IF NOT EXISTS linkables_by_entry ON linkables(entry_id);
CREATE INDEX IF NOT EXISTS sub_by_parent ON sub(parent_id, child_id);
CREATE INDEX IF NOT EXISTS sub_by_child ON sub(child_id, parent_id);
CREATE INDEX IF NOT EXISTS entries_by_title ON entries(title);
"""


def prepare_dictionary(db: Connection):
    check = "select 1 from sqlite_master where name='document_parts'"
    if db.execute(check).fetchone():
        return
    with db:
        db.execute("begin immediate")
        if db.execute(check).fetchone():
            return
        for statement in SCHEMA.strip().rstrip(";").split(";"):
            db.execute(statement)
        # Old pending flags didn't distinguish configuration changes from metadata updates.
        db.execute("update entries set needs_update=2 where needs_update=1")


_OPEN = re.compile(rb"""<[^"'<>]*(?:(?:"[^"]*"|'[^']*')[^"'<>]*)*>""")


@dataclass
class ImportEntries:
    archival: bool
    # Entry ID -> whether the stored definition had a preserving ancestor outside its XML.
    defined: dict[int, bool] = field(default_factory=dict)
    deferred: set[int] = field(default_factory=set)
    # Contextual schema IDs of nested definitions, for standalone copies in the same import.
    aliases: dict[int, str] = field(default_factory=dict)


@dataclass
class EntrySlot:
    start: int
    end: int = 0
    inherited: dict[str, str] = field(default_factory=dict)
    inherited_preserve: bool = False


@dataclass
class Document:
    data: bytes
    prolog_end: int = 0
    root_close: int = 0
    root_end: int = 0
    standalone_entry: bool = False
    declaration_end: int = 0
    archive_offset: int | None = None
    declaration_encoding: str | None = None
    doctype: str = ""
    entries: list[EntrySlot] = field(default_factory=list)
    max_entry_id: int = 0

    def markup(self, start: int, end: int | None = None) -> str:
        return self.data[start:end].decode("utf-8")

    def prolog(self, start: int = 0) -> str:
        end = self.prolog_end if self.archive_offset is None else self.archive_offset
        before = self.markup(start, end)
        if self.declaration_encoding and start == 0:
            declaration_end = len(self.markup(0, self.declaration_end))
            before = before[:declaration_end].replace(self.declaration_encoding, "UTF-8") + before[declaration_end:]
        if self.archive_offset is None:
            return before
        return before + self.markup(self.archive_offset + len(ARCHIVE_PI), self.prolog_end)


EntryPath = list[tuple[str, dict[str, str]]]


def read_document(data: bytes, entry_tag: str, *,
                  on_nested_id: Callable[[EntryPath, str, dict[str, str], str], None] | None = None) -> Document:
    """Locate editable entry spans, optionally reporting identified descendants of non-archive entries."""
    document = Document(data)
    parser = ParserCreate("utf-8")
    depth = 0
    active_depth = 0
    active = None
    empty = False
    root_empty = False
    doctype_start = 0
    scopes = [({}, False)]
    entry_path: EntryPath = []

    def start(name, attrs):
        nonlocal depth, active_depth, active, empty, root_empty, entry_tag
        depth += 1
        if depth == 1:
            document.prolog_end = parser.CurrentByteIndex
            root_open_end = _OPEN.match(data, document.prolog_end).end()
            root_empty = data[root_open_end - 2:root_open_end] == b"/>"
        if not entry_tag and depth == 2:
            entry_tag = name

        identifier = attrs.get("lxnm:id") or attrs.get("lxnm:entryID", "")
        if identifier and len(identifier) <= 19 and identifier.isascii() and identifier.isdigit():
            document.max_entry_id = max(document.max_entry_id, min(int(identifier), 2**63 - 1))
        if active is not None:
            if entry_path:
                if identifier and on_nested_id:
                    on_nested_id(entry_path, name, attrs, identifier)
                entry_path.append((name, attrs))
            return
        scope, inherited_preserve = scopes[-1]
        declared = {key: value for key, value in attrs.items() if key == "xmlns" or key.startswith("xmlns:")}
        namespaces = scope | declared if declared else scope
        scopes.append((namespaces, inherited_preserve or attrs.get("xml:space") == "preserve"))
        is_record = bool(identifier and (name != SUBENTRY) and namespaces.get("xmlns:lxnm", LXNM) == LXNM)
        if name == entry_tag or is_record:
            pos = parser.CurrentByteIndex
            opening = _OPEN.match(data, pos)
            if opening is None:
                raise ValueError("Expected a literal XML entry, rather than one generated by an entity.")
            active = EntrySlot(pos, inherited={key: value for key, value in scope.items() if key not in declared},
                               inherited_preserve=inherited_preserve)
            active_depth = depth
            if on_nested_id and document.archive_offset is None:
                entry_path.append((name, attrs))
            empty = data[opening.end() - 2:opening.end()] == b"/>"
            document.standalone_entry = depth == 1

    def end(name):
        nonlocal depth, active
        if entry_path:
            entry_path.pop()
        if active is not None and depth != active_depth:
            depth -= 1
            return
        pos = parser.CurrentByteIndex
        if active is not None:
            active.end = pos if empty else data.index(b">", pos) + 1
            document.entries.append(active)
            active = None
        if depth == 1:
            document.root_close = pos
            document.root_end = pos if root_empty else data.index(b">", pos) + 1
        depth -= 1
        scopes.pop()

    def xml_decl(version, encoding, standalone):
        document.declaration_end = data.index(b"?>", parser.CurrentByteIndex) + 2
        if encoding and encoding.lower() not in {"utf-8", "utf8", "us-ascii", "ascii"}:
            raise ValueError("Import XML encoded as UTF-8.")
        document.declaration_encoding = encoding if encoding and encoding.lower() in {"us-ascii", "ascii"} else None

    def start_doctype(*_):
        nonlocal doctype_start
        doctype_start = data.rindex(b"<!DOCTYPE", 0, parser.CurrentByteIndex)

    def end_doctype():
        document.doctype = document.markup(doctype_start, parser.CurrentByteIndex + 1)

    def external_entity(*_):
        raise ValueError("An external entity cannot be read during XML import.")

    def processing_instruction(target, data_string):
        if depth == 0 and not document.root_end and target == "lexonomy" and data_string == 'archive="1"':
            offset = parser.CurrentByteIndex
            if data.startswith(ARCHIVE_PI.encode(), offset):
                document.archive_offset = offset

    parser.ProcessingInstructionHandler = processing_instruction
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.XmlDeclHandler = xml_decl
    parser.StartDoctypeDeclHandler = start_doctype
    parser.EndDoctypeDeclHandler = end_doctype
    parser.ExternalEntityRefHandler = external_entity
    parser.Parse(data, True)
    return document


def export_document(db: Connection, rootname: str, *, clean: bool, flag: str | None,
                    transform: Callable[[str], str | None] | None) -> Iterator[str]:
    """Stream the document layout and its entries from one database snapshot."""
    # Anchor lookups and entry rows must see the same version during a streamed download.
    begin_snapshot = not db.in_transaction
    if begin_snapshot:
        db.execute("begin")
    try:
        boundary = dict(db.execute("select position, markup from document_parts where position < 0"))
        top_level = {row[0] for row in db.execute(
            "select entry_id from document_parts where entry_id is not null")}
        children = dict(db.execute(
            "select id, xml from entries where id in (select child_id from sub)"))
        defined = set()
        ancestors = set()

        def render(entry_id, xml):
            ancestors.add(entry_id)
            defined.add(entry_id)
            try:
                return rewrite(xml, flag=flag, clean=clean, resolve=resolve) if clean or children else xml
            finally:
                ancestors.remove(entry_id)

        def resolve(entry_id):
            if entry_id not in children or entry_id in ancestors:
                return None
            if not clean and (entry_id in defined or entry_id in top_level):
                return None
            result = render(entry_id, children[entry_id])
            if not clean:
                name_end = re.match(r"<([^\s/>]+)", result).end()
                result = result[:name_end] + f' {EMBEDDED}="true"' + result[name_end:]
            return result

        def render_root(entry_id, xml):
            result = render(entry_id, xml)
            return (transform(result) or result) if transform else result

        unplaced = """
            from entries e
            where not exists (select 1 from sub where child_id=e.id)
              and not exists (select 1 from document_parts where entry_id=e.id)
        """

        def render_unplaced():
            for entry_id, xml in db.execute("select id, xml " + unplaced + " order by id"):
                yield render_root(entry_id, xml)
                yield "\n"
            # A connected component consisting entirely of a reference cycle has no root.
            for entry_id, xml in children.items():
                if entry_id not in defined:
                    yield render_root(entry_id, xml)
                    yield "\n"

        last_slot = db.execute("select max(position) from document_parts where is_slot").fetchone()[0]
        standalone = boundary and not boundary[-2]
        wrap = not boundary or (standalone and (
            db.execute("select 1 " + unplaced + " limit 1").fetchone() or len(top_level) != 1
            or db.execute("select 1 from document_parts where position > 1 limit 1").fetchone()
        ))
        yield boundary.get(-3, "")
        if not clean:
            yield ARCHIVE_PI
        if wrap:
            yield f"<{rootname}>\n"
        for position, markup, entry_id, xml in db.execute("""
            select position, markup, e.id, e.xml from document_parts d
            left join entries e on e.id=d.entry_id where position > 0 order by position
        """):
            if markup:
                yield markup
            if entry_id is not None:
                yield render_root(entry_id, xml)
            if position == last_slot:
                yield from render_unplaced()
        if last_slot is None:
            yield from render_unplaced()
        if wrap:
            yield f"</{rootname}>\n"
        yield boundary.get(-2, "")
        yield boundary.get(-1, "")
    finally:
        if begin_snapshot:
            db.rollback()
