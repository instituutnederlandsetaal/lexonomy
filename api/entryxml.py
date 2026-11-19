"""Read stored XML without building the editable BeautifulSoup tree."""

import re
from collections.abc import Callable, Iterator
from lxml import etree

LXNM = "http://www.lexonomy.eu/"
SUBENTRY = "lxnm:subentryParent"
EMBEDDED = "lxnm:embedded"
ARCHIVE_PI = '<?lexonomy archive="1"?>'


def add_attributes(xml: str, doctype: str, attributes: str) -> str:
    name_end = len(doctype) + 1
    return xml[:name_end] + attributes + xml[name_end:]


# Comments, CDATA and processing instructions may contain text that looks like markup.
_LITERAL = r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<\?.*?\?>"
_ATTRIBUTES = r"""(?:[^"'<>]|"[^"]*"|'[^']*')*"""
_TOKEN = re.compile(
    rf"{_LITERAL}|</?(?P<name>[^\s/<>]+)(?=[\s/>])(?P<attributes>{_ATTRIBUTES})>",
    re.DOTALL,
)
_ATTRIBUTE = re.compile(r"""\s+([^\s=]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""")


def rewrite(xml: str, *, flag: str | None = None, clean: bool = False,
            resolve: Callable[[int | None], str | None] | None = None) -> str:
    """Rewrite only markup that needs to change. Leave text and unrelated markup as stored."""
    if (not clean or ("lxnm:" not in xml and (not flag or "<" + flag not in xml))) and (
        resolve is None or "<" + SUBENTRY not in xml
    ):
        return xml

    skip_until = False
    skip_replacement = ""
    depth = 0
    parts = []
    position = 0
    for match in _TOKEN.finditer(xml):
        name = match["name"]
        if name is None:
            continue
        closing = xml[match.start() + 1] == "/"
        empty = xml[match.end() - 2] == "/"
        if skip_until:
            if not empty:
                depth += -1 if closing else 1
            if depth == 0:
                position = match.end()
                parts.append(skip_replacement)
                skip_until = False
            continue
        if closing:
            continue
        if clean and flag == name and match.start() != 0:
            parts.append(xml[position:match.start()])
            position = match.end()
            if not empty:
                skip_until = True
                skip_replacement = ""
                depth = 1
            continue
        attributes = match["attributes"]
        if name == SUBENTRY:
            identifier = next((int(a or b) for key, a, b in _ATTRIBUTE.findall(attributes)
                               if key == "id" and len(a or b) <= 20 and (a or b).lstrip("-").isascii()
                               and (a or b).lstrip("-").isdigit()), None)
            replacement = resolve(identifier) if resolve is not None else None
            if replacement is not None or clean:
                parts.append(xml[position:match.start()])
                position = match.end()
                if empty:
                    parts.append(replacement or "")
                else:
                    skip_until = True
                    skip_replacement = replacement or ""
                    depth = 1
        elif clean and ("lxnm:" in attributes or "xmlns:lxnm" in attributes):
            filtered = _ATTRIBUTE.sub(
                lambda attr: "" if attr[1].startswith("lxnm:") or attr[1] == "xmlns:lxnm"
                else attr[0], attributes)
            parts.extend((xml[position:match.start()], "<", name, filtered, ">"))
            position = match.end()
    parts.append(xml[position:])
    return "".join(parts)


class EntryText:
    """Text fields from normalized entry XML. Qualified fields use the editable parser."""

    def __init__(self, xml: str):
        self.root = etree.fromstring(xml.encode(), etree.XMLParser(
            resolve_entities=False, no_network=True, collect_ids=False, strip_cdata=False))
        if self.root.nsmap.get(None) is not None:
            raise ValueError("Default namespaces require the qualified-name parser.")

    @staticmethod
    def simple_text(node):
        # BeautifulSoup's Tag.string follows chains of sole children.
        while len(node) == 1 and node.text is None and node[0].tail is None:
            node = node[0]
        return node.text if len(node) == 0 else None

    def texts(self, name: str) -> Iterator[str]:
        for node in self.root.iterdescendants(name):
            if (text := self.simple_text(node)) and (text := text.strip()):
                yield text

    def first(self) -> str | None:
        for text in self.root.itertext():
            if text := text.strip():
                return text
        return None
