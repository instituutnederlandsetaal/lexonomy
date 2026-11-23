#!/usr/bin/python3

from collections import defaultdict
from contextlib import ExitStack, closing
import datetime
import itertools
import json
import os
import os.path
from pyexpat import ExpatError, ParserCreate
import sqlite3
from sqlite3 import Connection
import hashlib
import random
import string
import smtplib, ssl
from email.message import EmailMessage
from typing import Any, Callable, Iterable, List, Literal, Optional, Tuple, TypedDict, Union, Set
from typing_extensions import NotRequired
from bs4 import BeautifulSoup, CData, Comment, NavigableString, Tag
from bs4.element import XMLProcessingInstruction
from lxml.etree import XMLSyntaxError
from xml.sax.saxutils import quoteattr
from entryxml import EMBEDDED, LXNM, EntryText, SUBENTRY, add_attributes, rewrite
from dictionary_document import ImportEntries, export_document, prepare_dictionary, read_document
import shutil
import markdown
import re
import secrets
import pathlib
from icu import Locale, Collator
from adminscripts.setup_admin import INITIAL_ADMIN
from siteconfig import API_DIR, load_siteconfig

class ConfigTitling(TypedDict):
    headword: NotRequired[str]
    """(xema) Element ID whose text to use as entry headword. Use the first text content in the entry if not supplied"""

    headwordSorting: NotRequired[str]
    """(optional) alternative (xema) ID for element to use for sorting."""

    sortDesc: bool
    """invert sort order?"""

    numberEntries: int
    """number of entries to load in the sidebar by default. defaults to 1000 (when frontend generates config)"""

    locale: str
    """collator locale to use for sorting"""

    headwordAnnotationsType: Literal['simple', 'advanced']
    """"Which of headwordAnnotations or headwordAnnotationsAdvanced to use. If advanced and headwordAnnotationsAdvanced is empty, fall back to normal headwordAnnotations property"""

    headwordAnnotations: NotRequired[List[str]]
    """List of element IDs (not names!) whose text to put in the entry's title"""

    headwordAnnotationsAdvanced: NotRequired[str]
    """a format string like "<some_html>%(element_name)</some_html><some_more_html>%(another_element_name)</some_more_html>"
    %() escape-codes will be substituted with the text contents of the first element with that name in the entry"""

class ConfigSearchability(TypedDict):
    searchableElements: NotRequired[List[str]]
    """List of element names whose text to extract and index as searchable strings for entries"""

class ConfigLinksEntry(TypedDict):
    """Elements listed here can be used as target of cross-reference link.
    For each element, specify unique identifier in the form of placeholders <tt>'%(element)'</tt>.
    Eg. element <tt>entry</tt> can have identifier <tt>%(lemma)-%(pos)</tt>, element <tt>sense</tt> can have identifier <tt>%(lemma)-%(number)</tt>.
    Optionally, specify element you want to show as preview when selecting links.</p>"""

    linkElement: str
    """Element name .e.g. "entry"""""

    identifier: str
    """a format-string with sequences like %(element_name)"""

    preview: str
    """(optionally) element you want to show as preview when selecting links."""

class ConfigFlaggingEntry(TypedDict):
    key: str
    "Keyboard shortcut" # TODO document format
    name: str
    "Value in the flag element e.g. \"unpublished\""
    label: str
    "User friendly label"
    color: str
    "Css color string, usually in the format of #RRGGBB. Color of a small icon next to entries with this flag in the entry list."

class ConfigFlagging(TypedDict):
    flag_element: str
    "Name of the element in which to store the flag. Element doesn't have to exist, if it doesn't the entry does not have a flag."
    flags: list[ConfigFlaggingEntry]

class ConfigXemaElementChild(TypedDict):
    min: int | str
    max: int | str | None
    name: str
    """An ID in xema["elements"] where the child info is held."""

class ConfigXemaAttributeValue(TypedDict):
    value: str
    caption: str

class ConfigXemaAttribute(TypedDict):
    optionality: Literal["optional", "obligatory"]
    filling: Literal["txt", "lst"]
    values: NotRequired[list[ConfigXemaAttributeValue] | None]

class ConfigXemaElement(TypedDict):
    elementName: NotRequired[str | None]
    """When supplied, use this as xml tag instead of the key in the xema["elements"].
        This can be useful when the xml contains elements with the same name that require a different configuration.

        E.G.:
        xema = {
            elements: {
                some_element: { }, # no name is set, so we use the key as xml element: <some_element>...</some_element>
                some_other_element: { elementName: "some_element" } # now we have an elementName property, so use that: <some_element>...</some_element>
            }
        }

        But now how to know which ID matches with an element, since multiple configured elements can set the same elementName?
        Check the parent. Only one of a parent children (i.e. siblings) should ever have a given elementName.
     """
    filling: NotRequired[Literal["inl", "txt", "chd", "emp", "lst", "med"]]
    values: NotRequired[list[ConfigXemaAttributeValue]]
    children: NotRequired[list[ConfigXemaElementChild]]
    attributes: NotRequired[dict[str, ConfigXemaAttribute]]


class ConfigXema(TypedDict):
    root: str
    elements: dict[str, ConfigXemaElement]
    _dtd: NotRequired[str]
    _newXml: NotRequired[str]
    _xonomyDocSpec: NotRequired[str]
    newXml: NotRequired[str]

# Keys are duplicated in the entry, using the linkElement property: so { "entry": {"linkElement": "entry", ...etc} }
ConfigLinks = dict[str, ConfigLinksEntry]

class ConfigSubentryTitling(TypedDict):
    headword: str
    """ID of the (xema) element to use as headword/title for the subentry.
    We will fall back to using the first text content in the entry if not supplied.
    """

class ConfigSubbingEntry(TypedDict, total=False):
    attributes: dict[str, str]
    """A dictionary containing: { [name of attribute]: "required value of attribute" } (if empty value - only presence of attribute is checked, any value is accepted)
        The attributes property is NotRequired because this setting didn't always exist, and so it won't be there in old configs.
    """
    titling: Optional[ConfigSubentryTitling]
    """Titling configuration for the subentry."""
    

ConfigSubbing = dict[str, ConfigSubbingEntry] # values are empty dicts for now

class ConfigIdent(TypedDict):
    "Dictionary info: title, description etc."
    title: str
    blurb: str
    lang: str
    handle: str
    "Link to external metadata handle?. Usually empty string?"

class ConfigUsersUser(TypedDict):
    "User information in the context of the current dictionary"
    canEdit: bool
    canConfig: bool
    canDownload: bool
    canUpload: bool

ConfigUsers = dict[str, ConfigUsersUser]

class ConfigPublico(TypedDict):
    "Publishing information of a dictionary"
    public: bool
    licence: str

# Alternative syntax due to illegal key names
ConfigMetadata = TypedDict('ConfigMetadata', {
    'dc.title': NotRequired[str],
    'dc.language.iso': NotRequired[str],
    'dc.rights': NotRequired[str]
})

class ConfigDownload(TypedDict):
    xslt: NotRequired[str]
    "xslt to apply to exported/downloaded entry xml"

class ConfigAutoNumbering(TypedDict):
    """Given an element to count, and a place to put the number of occurances (or """

    element: str
    """Element to count, or where to evaluate string_template.
        Unless 'target' property is set, any contents of this element are also replaced with the result (so either the count or the evaluated string_template).
    """
    target: NotRequired[str]
    """(optional) Alternative place to put the Value, can be a child element or an attribute.
        Attributes are denoted by a leading '@', so '@some_attribute'. The attribute is added to the element denoted by the 'element' setting.
        Child elements are just the name of the target element, so 'some_child_element'.
        Element and attribute are created if missing.
    """

    type: NotRequired[Literal["string", "number"]]
    """Whether to write numbers or use the string_template to create a textual ID. Defaults to 'number'"""
    string_template: Optional[str]
    """Only used if type == "string".
        The format string to use to generate textual ids - takes the shape of %(some-element) $(@some-attribute).
    """
    number_globally: NotRequired[bool]
    """Only used if type == 'number'
        Whether to keep incrementing the IDs, or restart at 0 every entry
    """
    number_next: NotRequired[int]
    """Only used if type == 'number' and 'number_globally' == True
        The next number to output. Should be saved across runs
    """
    overwrite_existing: NotRequired[bool]
    """Whether to overwrite existing values in the target element/attribute.
        Does not apply when auto_apply = True and type = "number" and number_globally = True, as that would case ids to increase every single time an entry is updated.
    """
    auto_apply: NotRequired[bool]
    "Whether to automatically perform this autonumbering on entry saving, or only as a one-off manual operation"




class Configs(TypedDict):
    titling: ConfigTitling
    subbing: ConfigSubbing
    searchability: ConfigSearchability
    links: ConfigLinks
    flagging: ConfigFlagging
    xema: ConfigXema
    xemplate: Any # TODO add typing information.
    users: ConfigUsers
    "Keyed by user email address"
    ident: ConfigIdent
    publico: ConfigPublico
    metadata: ConfigMetadata
    download: ConfigDownload
    autonumbering: dict[str, ConfigAutoNumbering]

# Other types
class IsoCode(TypedDict):
    code: str
    code3: str
    lang: str

class ListedUser(TypedDict):
    id: str
    "user email"
    title: str
    "also user email"

class UserList(TypedDict):
    entries: List[ListedUser]
    total: int

class Historiography(TypedDict):
    uploadStart: NotRequired[str]
    "str(datetime.datetime.utcnow())"
    filename: NotRequired[str]
    "Path of the newly uploaded file (after saving as tempfile on the server) when uploading a dictionary and purging the old data."
    viaApi: NotRequired[bool]

class EntryRendering(TypedDict, total=False):
    contentHtml: str
    resolvedXml: str

class HistoryEntry(EntryRendering):
    entry_id: int
    revision_id: int
    content: str
    "xml content"
    action: Literal["create", "update", "delete", "purge"]
    when: int
    "UTC time? DATETIME in sqlite"
    email: str
    "Can be empty"
    historiography: Historiography
    schemaId: NotRequired[str]

class RelatedEntry(TypedDict):
    "Related entry in dictionary - parent- or child/sub-entry "
    id: int
    title: str
    doctype: str

class EntryFromDatabase(TypedDict):
    id: int
    title: str
    sortkey: str
    flag: str
    """Flag is "" when entry not flagged."""
    doctype: str
    "Xml name of the root node"
    subentries: List[RelatedEntry]
    parententries: List[RelatedEntry]
    # Optionals
    xml: NotRequired[str]
    content: NotRequired[str]
    tag: NotRequired[Tag]
    titlePlain: NotRequired[str]
    schemaId: NotRequired[str]

class User(TypedDict):
    email: str
    loggedin: bool
    isAdmin: NotRequired[bool]

siteconfig = load_siteconfig()
for datadir in ["dicts", "uploads", "sqlite_tmp"]:
    pathlib.Path(os.path.join(siteconfig["dataDir"], datadir)).mkdir(parents=True, exist_ok=True)
os.environ["SQLITE_TMPDIR"] = os.path.join(siteconfig["dataDir"], "sqlite_tmp")

defaultDictConfig = {
    "editing": {
        "xonomyMode": "nerd",
        "xonomyTextEditor": "askString"
    },
    "searchability": {
        "searchableElements": []
    },
    "xema": {
        "elements": {}
    },
    "titling": {
        "headwordAnnotations": []
    },
    "flagging": {
        "flag_element": "",
        "flags": []
    }
}

prohibitedDictIDs = {
    "login", "logout", "make", "signup", "register", "forgot", "forgotpwd",
    "changepwd", "users", "dicts", "oneclick", "recoverpwd", "createaccount",
    "consent", "userprofile", "dictionaries", "opendictionaries", "about",
    "list", "lemma", "json", "ontolex", "tei", "e404", "",
}

# db management
def getDB(dictID: str, *, prepare: bool = True) -> Connection:
    if os.path.isfile(os.path.join(siteconfig["dataDir"], "dicts", dictID+".sqlite")):
        conn = sqlite3.connect(os.path.join(siteconfig["dataDir"], "dicts", dictID+".sqlite"))
        conn.row_factory = sqlite3.Row
        conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=on; PRAGMA busy_timeout = 5000;")
        if prepare:
            prepare_dictionary(conn)
        return conn
    else:
        raise FileNotFoundError(f"Database for dictionary {dictID} not found")

def getMainDB():
    conn = sqlite3.connect(os.path.join(siteconfig["dataDir"], 'lexonomy.sqlite'))
    conn.row_factory = sqlite3.Row
    conn.executescript("PRAGMA busy_timeout = 5000;")
    return conn

def getLinkDB():
    conn = sqlite3.connect(os.path.join(siteconfig["dataDir"], 'crossref.sqlite'))
    conn.row_factory = sqlite3.Row
    return conn

# SMTP
def sendmail(mailTo: str, mailSubject: str, mailText: str):
    if siteconfig["mailconfig"] and siteconfig["mailconfig"]["host"] and siteconfig["mailconfig"]["port"]:
        if siteconfig["mailconfig"]["secure"]:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(siteconfig["mailconfig"]["host"], siteconfig["mailconfig"]["port"], context=context)
        else:
            server = smtplib.SMTP(siteconfig["mailconfig"]["host"], siteconfig["mailconfig"]["port"])
        
        # Create RFC 5322 compliant message with proper headers
        msg = EmailMessage()
        msg['Subject'] = mailSubject
        msg['From'] = siteconfig["mailconfig"]["from"]
        msg['To'] = mailTo
        msg.set_content(mailText)
        
        server.send_message(msg)
        server.quit()


# config
RETIRED_DICT_CONFIGS = {"ske", "kex", "kontext", "xampl", "thes", "collx", "defo", "gapi"}

def readDictConfigs(dictDB: Connection) -> Configs:
    configs = {}
    c = dictDB.execute("select * from configs")
    for r in c.fetchall():
        if r["id"] not in RETIRED_DICT_CONFIGS:
            configs[r["id"]] = json.loads(r["json"])
    for conf in ["ident", "publico", "users", "titling", "flagging",
                 "searchability", "xema", "xemplate", "editing", "subbing",
                 "download", "links", "autonumber", "metadata", "autonumbering"]:
        if not conf in configs:
            configs[conf] = defaultDictConfig.get(conf, {})

    users = {}
    for email in configs["users"]:
        users[email.lower()] = configs["users"][email]
    configs["users"] = users

    for key in configs.keys():
        if type(configs[key]) is dict:
            configs[key] = defaultdict(lambda: None, configs[key])

    return configs

# auth
def verifyLogin(email: str, sessionkey: str):
    with getMainDB() as conn:
        now = datetime.datetime.utcnow()
        yesterday = now - datetime.timedelta(days=1)
        email = email.lower()
        c = conn.execute("select consent from users where email=? and sessionKey=? and sessionLast>=?", (email, sessionkey, yesterday))
        user = c.fetchone()
        if not user:
            return {"loggedin": False, "email": None}
        conn.execute("update users set sessionLast=? where email=?", (now, email))
        conn.commit()
        return {"loggedin": True, "email": email, "isAdmin": email in siteconfig["admins"],
            "consent": user["consent"] == 1}

def verifyLoginAndDictAccess(email: str, sessionkey: str, dictDB: Connection):
    ret = verifyLogin(email, sessionkey)
    configs = readDictConfigs(dictDB)
    dictAccess = configs["users"].get(ret["email"])
    if ret["loggedin"] == False or (not dictAccess and not ret["isAdmin"]):
        return ({
            "loggedin": ret["loggedin"], 
            "email": ret["email"] or "",
            "dictAccess": False, 
            "isAdmin": False
        }, configs)
    ret["dictAccess"] = {}
    for r in ["canEdit", "canConfig", "canDownload", "canUpload"]:
        ret[r] = bool(ret.get("isAdmin") or (dictAccess and dictAccess.get(r)))
        ret["dictAccess"][r] = ret[r]
    return ret, configs

# also used as default sort key and default title/entry label
DEFAULT_HEADWORD = "?"


# utils

def xema_get_element_name_from_id(xema: ConfigXema, elementID: str) -> str:
    """Xema elements no longer keyed by their xml tag name. Now keyed by an arbitrary ID. Util function to convert one to the other."""
    return xema["elements"].get(elementID, {}).get("elementName", elementID) or elementID

def xema_get_id_from_element_name(xema: ConfigXema, elementName: str, parentElementID: Optional[str] = None) -> str:
    """Xema elements no longer keyed by their xml tag name. Now keyed by an arbitrary ID. Util function to convert one to the other.
    Parent is used to disambiguate (because multiple elements may specify the same elementName value, but elementName is unique among siblings.
    That means if you use this without specifying the parent, and the elementName is not the entry's root node, you're doing it wrong.
    """

    # Since there mayb be multiple elements where this is true, use the parent to disambiguate (if supplied).
    parentElement: Optional[ConfigXemaElement] = xema["elements"].get(parentElementID) if parentElementID else None
    if parentElement:
        for childConfig in parentElement.get("children", []):
            childElementID = childConfig["name"]
            childElementName = xema_get_element_name_from_id(xema, childElementID)
            if childElementName == elementName:
                return childElementID

    # No parent supplied, or not found: return the root if it matches
    if root := xema.get("root"):
        if xema_get_element_name_from_id(xema, root) == elementName:
            return root

    # Root also didn't match: check all elements to see which it is (maybe an orphan element? (not the root, but no parent either.))
    for thisElementID in xema["elements"]:
        if xema_get_element_name_from_id(xema, thisElementID) == elementName:
            return thisElementID

    # Nothing in the entire Xema uses the requested elementName - so the config is technically in an invalid state. Use a sensible default I guess.
    return elementName

XEMA_DEFINITION_ATTRIBUTE = "lxnm:definition"

def entry_schema_id(configs: Configs, xml: Tag) -> str:
    definition = xml.get(XEMA_DEFINITION_ATTRIBUTE)
    return schema_id_for_tag(configs, xml.name, definition if isinstance(definition, str) else None)


def schema_id_for_tag(configs: Configs, name: str, definition: str | None = None) -> str:
    xema = configs["xema"]
    if definition in configs["subbing"] and xema_get_element_name_from_id(xema, definition) == name:
        return definition
    root = xema.get("root")
    if root and xema_get_element_name_from_id(xema, root) == name:
        return root
    matches = [key for key in configs["subbing"] if xema_get_element_name_from_id(xema, key) == name]
    return matches[0] if len(matches) == 1 else xema_get_id_from_element_name(xema, name)


# Use the editable parser when comments/CDATA affect string boundaries or a config uses literal prefixes.
EDITABLE_MARKUP = re.compile(r"xmlns\s*=|<!|<\?|</?(?!lxnm:subentryParent[\s/>])[^\s/>:]+:")


def quick_entry_text(xml: str) -> EntryText | None:
    if not EDITABLE_MARKUP.search(xml):
        try:
            return EntryText(xml)
        except (ValueError, XMLSyntaxError):
            pass
    return None


def index_fields(configs: Configs, xml: str, doctype: str) -> tuple[Tag | EntryText, str]:
    if fields := quick_entry_text(xml):
        definition = fields.root.get(f"{{{LXNM}}}definition")
        return fields, schema_id_for_tag(configs, doctype, definition)
    tag = parse(xml)
    return tag, entry_schema_id(configs, tag)


def parse(xml: str, *, doctype: str = "") -> Tag:
    """Parse the xml and return the entry its root node. Expects to be passed xml with a single root node."""
    # We roll our own builder because all existing beatifulsoup parsers have some drawback that make them unusable in our context:
    # 1. lxml lowercases and expands self-closing elements e.g. <Test/> -> <test></test>
    # 2. lxml-xml removes unbound namespaces e.g. <mynamespace:element> -> <element> when mynamespace is not declared.
    #    which can often happen because we're not processing entire documents, only fragments,
    #    and so the element where the namespace was declared (usually the dictionary root) is not part of the xml string here.
    #    It's bad behavior to just remove random user namespaces, especially as the dictionary may be from a toolset that relies on them.
    # 3. html does...many things, lowercase elements, mess with attributes, etc. It's not an xml parser after all.

    # So what we do:
    # Treat namespace prefixes as if they're just part of the element or attribute name.
    # This means that to match a namespaced element, the query should just include the prefix: e.g. xml.findAll('lxnm:subentryParent')

    # There are a few (small) drawbacks to this method, listed here:
    # 1. we cannot tell what uri a namespace prefix is bound to, so it may be possible there is a "lxnm" namespace DIFFERENT from the lexonomy one,
    #    we then erroneously assume elements in that namespace are ours, and use them, IF they have the same name as ours.
    #    However I consider this bad-faith input, so we will disregard this possibility.
    # 2. Since we're not namespace-aware, if sections of the xml are put in a namespace without using "namespace:" prefixes, we miss that, and assume they are in the global namespace.
    #    Example:
    #    <entry>
    #        <headword>example</headword>
    #        <some_other_content xmlns="foo"> <!-- this and everything inside is "foo" namespace, but lexonomy doesn't know because no "foo:" prefix  -->
    #            <headword>headword in the "foo" namespace.</headword>
    #        </some_other_content>
    #    </entry>
    b: Any = BeautifulSoup()

    p = ParserCreate("utf-8")
    p.buffer_text = True
    in_cdata = False

    def start_element(name: str, attrs: Any):
        b.handle_starttag(name, attrs=attrs, nsprefix=None, namespace=None, sourceline=p.CurrentLineNumber, sourcepos=p.CurrentColumnNumber)

    def end_element(name: str):
        b.handle_endtag(name)

    def char_data(data: str):
        if b.currentTag is not b:
            b.object_was_parsed(CData(data) if in_cdata else NavigableString(data))

    def cdata(active: bool):
        nonlocal in_cdata
        in_cdata = active

    def comment(data: str):
        if b.currentTag is not b:
            b.object_was_parsed(Comment(data))

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    p.StartCdataSectionHandler = lambda: cdata(True)
    p.EndCdataSectionHandler = lambda: cdata(False)
    p.CommentHandler = comment
    p.ProcessingInstructionHandler = lambda target, data: (
        b.object_was_parsed(XMLProcessingInstruction(f"{target} {data}" if data else target)) if b.currentTag is not b else None
    )
    if doctype:
        p.Parse(doctype, False)
    p.Parse(xml, True)
    return list(b.children)[0]

def doSql(db: Connection, sql: str, param: Any = None):
    """Convenience to enable easy logging of sql statements during development"""
    return db.execute(sql, param)

def deleteEntry(dictDB: Connection, configs: Configs, id: int, email: Optional[str]):
    """"
        Delete an entry (or subentry).
        When deleting a subentry, any parent entries will be patched to remove the link with the subentry.
        Why is the link deleted instead of replaced with a copy of the subentry contents?
            well: otherwise, after the parent is updated, the subentry would just automatically re-create itself from the inserted content
    """

    for parent in doSql(dictDB, "select entries.id, xml from entries left join sub on entries.id = sub.parent_id where sub.child_id=?", (id, )).fetchall():
        parentXml = parse(parent["xml"])
        parentId = parent["id"]
        for reference in parentXml.find_all("lxnm:subentryParent", attrs={"id": str(id)}):
            reference.decompose() # removes the element
        createEntry(dictDB, configs, parentXml, email="system@lexonomy", id=parentId, commit=False)

    # tell history that I have been deleted:
    dictDB.execute("insert into history(entry_id, action, [when], email, xml) values(?,?,?,?,?)",
                (id, "delete", datetime.datetime.utcnow(), email, None))
    doSql(dictDB, "delete from entries where id=?", (id, )) # rows in the "sub" table linking with any parents should cascade.
    dictDB.commit()

def get_xslt_transformer(xsl: Optional[str]) -> Callable[[str], Optional[str]]:
    """
    Compile the xslt, return a function that runs it on the passed xml and returns the result.
    The returned function will return None when: xslt cannot be parsed/xml cannot be parsed/no xslt was supplied.

    Example: getXsltTransformer(myOptionalXslt)(myXml) or myXml # get and run transformer, return the untransformed xml if something went wrong.\
    """
    import lxml.etree as ET

    def no_op(xml: str) -> None:
        return None

    if not xsl:
        return no_op

    class NoExternalDocuments(ET.Resolver):
        def resolve(self, url, public_id, context):
            raise OSError("Stylesheets cannot load external resources")

    parser = ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    parser.resolvers.add(NoExternalDocuments())
    try:
        xsl_dom = ET.XML(xsl.encode(), parser=parser)
        xslt = ET.XSLT(xsl_dom, access_control=ET.XSLTAccessControl.DENY_ALL)
    except (ET.LxmlError, OSError, ValueError):
        return no_op

    def run_xslt(xml: str) -> Optional[str]:
        """Run the xslt if possible, otherwise return None"""
        try:
            xml_dom = ET.XML(xml, parser=parser)
            html_dom = xslt(xml_dom)
            html_string = ET.tostring(html_dom, xml_declaration=False, encoding="utf-8").decode("utf-8")
            return html_string
        except (ET.LxmlError, OSError, ValueError):
            return None
    return run_xslt

class SortableEntry(TypedDict):
    sortkey: str
    id: int

def sortEntries(configs: Configs, sortables: List[SortableEntry], reverse: bool = False) -> List[SortableEntry]:
    "Sort the entries in the list by their sortkey. Uses the collator specified in the titling config. The list sorted in-place and returned for convenience."
     # sort by selected locale
    collator = Collator.createInstance(Locale(configs.get("titling", {}).get("locale", "en") or "en"))
    sortables.sort(key=lambda x: collator.getSortKey(x["sortkey"]), reverse=reverse)
    return sortables

def searchEntries(
    dictDB: Connection,
    configs: Configs,

    doctype: str,
    flag: Optional[str],
    searchtext: Optional[str],
    modifier: Optional[Literal["start", "wordstart", "substring", "exact"]] = "start",
    sortdesc: Union[str, bool] = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> Tuple[int, List[SortableEntry]]:
    """Retrieve entries sorted by sortkey. Optionally filtered by their headword.

    Args:
        dictDB (Connection): the db for the dictionary
        configs (Configs): configs for the dictionary
        doctype (str): doctype of the entries to retrieve. Usually the root element, but might be different when requesting subentries.
        flag (Optional[str]): find only entries with the given flag
        searchtext (Optional[str]):
        modifier (Optional[Literal["start", "wordstart", "substring", "exact"]], optional): Defaults to "start".
        sortdesc (Union[bool, str], optional): Reverse the usual sort order? The usual sort order is determined by ConfigTitling["sortDesc"]
        limit (Optional[int], optional): Limit the returned results to this number (when > 0)
        offset (int, optional): Skip this many results before returning. Defaults to 0.
    Returns:
        Tuple[int, List[SortableEntry]]: the total number of results, and the limited list of results.
    """
    if not searchtext:
        searchtext = ""
        modifier = None # can't search parts of words when not searching at all.
    searchtext = searchtext.lower()

    if type(sortdesc) == str:
        sortdesc = sortdesc == "true"
    if configs["titling"].get("sortDesc", False): # if default sort is inverted also invert descending
        sortdesc = not sortdesc

    where = " where doctype = ? "
    params = (doctype, )

    if flag:
        where = where + " and flag = ? "
        params = params + (flag, )

    if modifier == "start":
        where = where + " and s.txt like ? "
        params = params + (searchtext+"%", )
    elif modifier == "wordstart":
        where = where + " and (s.txt like ? or s.txt like ?) "
        params = params + (searchtext + "%", "% " + searchtext + "%")
    elif modifier == "substring":
        where = where + " and s.txt like ? "
        params = params + ("%" + searchtext + "%",)
    elif modifier == "exact":
        where = where + " and s.txt=? "
        params = params + (searchtext, )
    else: # default: searchtext not used
        pass

    sql = f"select distinct e.id, e.sortkey from searchables as s inner join entries as e on e.id=s.entry_id {where} group by e.id order by s.level"
    results: List[SortableEntry] = []
    for r in dictDB.execute(sql, params).fetchall():
        results.append({"id": r["id"], "sortkey": r["sortkey"]})

    results = sortEntries(configs, results, reverse=sortdesc)
    total = len(results)
    if (limit is not None and int(limit) > 0):
        results = results[offset:offset + int(limit)]
    elif offset > 0:
        results = results[offset:]
    return total, results

def readEntries(dictDB: Connection, configs: Configs, ids: Union[int, List[int], List[SortableEntry]], xml: bool=True, tag: bool=False, titlePlain: bool = False, sortdesc: Union[str, bool] = False) -> List[EntryFromDatabase]:
    """Read entries from the database, optionally returning some computed values with them.
    Entries requiring an update (due to changed config or related entries) are updated prior to returning.
    Entries are returned sorted according to their sortKey

    Args:
        dictDB (Connection):
        configs (Configs):
        ids (Tuple[int, List[int]]): either a single id or list of ids to retrieve. Maxes out at something like 500k, due to statement length limitations.
        xml (bool, optional): Also return the xml as string. Defaults to True.
        tag (bool, optional): Also return the xml as parsed. Defaults to False.
        titlePlain (bool, optional): Also include the plain text of the entry. This requires the xml to be parsed, so is slow.
        sortdesc (Union[bool, str], optional): Reverse the usual sort order? The usual sort order is determined by ConfigTitling["sortDesc"]
    Returns:
        List[EntryFromDatabase]: List of the entries.
    """

    if not isinstance(ids, list):
        ids = [ids]
    if len(ids) > 0 and not isinstance(ids[0], int):
        ids = list(map(lambda x: x["id"], ids))

    if type(sortdesc) == str:
        sortdesc = sortdesc == "true"
    if configs["titling"].get("sortDesc", False): # if default sort is inverted also invert descending
        sortdesc = not sortdesc

    if ids:
        reindex_entries(dictDB, ids=ids)

    rows = dictDB.execute(f"""
        select e.id, e.doctype, e.xml, e.title, e.sortkey, e.flag,
               (select json_group_array(json_object('id', c.id, 'title', c.title, 'doctype', c.doctype))
                from sub join entries c on c.id=sub.child_id where sub.parent_id=e.id) as children,
               (select json_group_array(json_object('id', p.id, 'title', p.title, 'doctype', p.doctype))
                from sub join entries p on p.id=sub.parent_id where sub.child_id=e.id) as parents
        from entries e where e.id in ({",".join("?" * len(ids))})
    """, ids).fetchall()

    entries: List[EntryFromDatabase] = []
    for row in rows:
        ret: EntryFromDatabase = {
            "id": row["id"],
            "title": row["title"],
            "sortkey": row["sortkey"],
            "flag": row["flag"],
            "subentries": json.loads(row["children"] or "[]"),
            "parententries": json.loads(row["parents"] or "[]"),
            "doctype": row["doctype"]
            # "success": True
        }
        if xml:
            ret["xml"] = row["xml"]
            ret["content"] = row["xml"]
        if tag:
            parsed = parse(row["xml"])
            ret["tag"] = parsed
            ret["schemaId"] = entry_schema_id(configs, parsed)
            if titlePlain:
                ret["titlePlain"] = get_entry_title(parsed, configs, ret["schemaId"])[0]
        elif titlePlain:
            fields, definition = index_fields(configs, row["xml"], row["doctype"])
            ret["schemaId"] = definition
            ret["titlePlain"] = get_entry_title(fields, configs, definition)[0]
        entries.append(ret)
    sortEntries(configs, entries, sortdesc)  # type: ignore - SortableEntry is a subset of Entry so this always works
    return entries

def get_entry_rendering(dictDB: Connection, xml: str | Tag, run_xslt: Callable[[str], Optional[str]]) -> EntryRendering:
    xml = str(resolveSubentries(dictDB, xml))
    html = run_xslt(xml)
    return {"contentHtml": html} if html else {"resolvedXml": xml}

def fixup_namespaces(xml: Tag):
    xml.attrs['xmlns:lxnm'] = 'http://www.lexonomy.eu/'

def get_entry_id(xml: Tag, dictDB: Connection, maybeID: Optional[int] = None) -> tuple[int, bool]:
    """
    Ensure the entry has a row in the database, and the entry root has an attribute @xml:id with the row ID.

    The ID is determined as such (first match):
    - 1. if an ID is passed, that will always be used, and the entry's xml will be updated to have that ID
    - 2. if no ID is passed, but the xml root has an @lxnm:id attribute, that will be used
    - 3. if no ID is passed and xml doesn't have @lxnm:id, a new id will be created and added to the xml.

    Returns ID, is new ID in database
    """
    if maybeID is not None: # id is passed in - update the xml to reflect.
        xml.attrs["lxnm:id"] = str(maybeID)
        id = None

    id = xml.attrs.get('lxnm:id') # check if xml has an id, if not, create one.
    if id is None:
        id = xml.attrs.get('lxnm:entryID') # id used to be stored in lxnm:entryID once upon a time: legacy support
    if id is not None:
        try:
            id = int(id)
        except:
            print(f"Invalid ID (non-number) {id} in to-be-imported entry: replacing...")
            if "lxnm:id" in xml.attrs:
                del xml.attrs["lxnm:id"]
            if "lxnm:entryID" in xml.attrs:
                del xml.attrs["lxnm:entryID"]
            id = None

    isNewEntry: bool = False
    if id is None: # let db create one
        id = doSql(dictDB, "insert into entries(doctype, xml, title, sortkey) values(?, ?, ?, ?)", ("", "", "", "")).lastrowid
        isNewEntry = True
    else:
        # ensure row exists
        isNewEntry = doSql(dictDB, "insert into entries(id, doctype, xml, title, sortkey) values(?,?,?,?,?) on conflict(id) do nothing", (id, "", "", "", "")).rowcount > 0

    xml.attrs["lxnm:id"] = str(id)
    if "lxnm:entryID" in xml.attrs: # delete legacy id attribute
        del xml.attrs["lxnm:entryID"]
    return id, isNewEntry

def is_subentry(config: ConfigSubbing, el: Tag | dict[str, str], element_id: str) -> bool:
    """Match the resolved schema definition and an optional attribute rule."""
    rule = config.get(element_id)
    if rule is None:
        return False
    required_attributes = rule.get("attributes") or {}
    return not required_attributes or any(
        el.get(name) is not None and (not value or el.get(name) == value)
        for name, value in required_attributes.items()
    )


def presave_subentries(dictDB: Connection, configs: Configs, entryXml: Tag, entryID: int, email: str, definition_id: str,
                        *, maintenance=False, importing: ImportEntries | None = None,
                        inherited_preserve: bool = False):
    """
    Ensure this entry has all subentries properly extracted and referenced through xml and database.
    Also flag any parent entries for needs_update.

    1. Find elements that should be a subentry (their tag is in the subbing config)
    2. Extract the element and its childen, and store it as a separate entry in the database
    3. Add back a <lxnm:subentryParent id="{idOfTheSeparateEntry}"/> xml placeholder element in this entry
    4. Fixup any remaining invalid references
        1. If the target has been updated and is still a valid subentry otherwise:
            Fixup the title and doctype on the <lxnm:parentEntry>
        2. If the entry it points to exists in the database, but is no longer allowed to be a subentry (due to changed attributes, doctype, etc?):
            replace it with a copy of that xml (removing lexonomy bookkeeping attributes in the copy)
        3. If it points to an entry that doesn't exist in the database:
            delete the tag.
            Keeping the tag is not an option, because we cannot save a link to a nonexistant entry due to referential constraints in the database.
            If we would keep the tag, but not save the reference in the database, that would give issues if the missing subentry was later created, perhaps by automatic assignment of an id.

    Finally save all parent->child references in the database.

    NOTE: changes stay within this entry.
    If this entry was once a subentry, but is now no longer (due to config changes), parents of this entry will need a separate update,
    this function will only modify subentries inside this entry, not modify entries that have this entry as subentry.
    """

    config = configs["subbing"]
    xema = configs["xema"]
    extracted: list[tuple[Tag, str, bool]] = []
    existing: dict[int, list[tuple[Tag, str]]] = defaultdict(list)

    def collect(node, parent_id, inherited_preserve):
        preserve = inherited_preserve or node.get("xml:space") == "preserve"
        for child in node.find_all(recursive=False):
            if child.name == "lxnm:subentryParent":
                existing[int(child["id"])].append((child, parent_id))
                continue
            child_id = xema_get_id_from_element_name(xema, child.name, parent_id)
            if importing is not None and importing.archival:
                extract = child.attrs.pop(EMBEDDED, None) == "true"
                if extract:
                    child_id = entry_schema_id(configs, child)
            else:
                extract = is_subentry(config, child, child_id)
            if extract:
                extracted.append((child, child_id, preserve))
            else:
                collect(child, child_id, preserve)

    if config or entryXml.find(SUBENTRY) or (importing is not None and importing.archival):
        collect(entryXml, definition_id, inherited_preserve)
    validSubentryIDs: set[int] = set()
    for child, child_id, preserve in extracted:
        for ancestor in child.parents:
            if not ancestor.name or ancestor.name == "[document]":
                break
            for name, value in ancestor.attrs.items():
                if name == "xmlns" or name.startswith("xmlns:"):
                    child.attrs.setdefault(name, value)
        subentry_id, subentry, success, _ = createEntry(
            dictDB, configs, child, email, commit=False, xema_element_id=child_id,
            maintenance=maintenance, importing=importing, inherited_preserve=preserve)
        if success:
            title = get_entry_title(subentry, configs, xema_element_id=child_id)[0]
            marker = BeautifulSoup().new_tag("lxnm:subentryParent", attrs={
                "id": str(subentry_id), "title": title, "doctype": get_entry_doctype(subentry)
            })
            child.replace_with(marker)
            validSubentryIDs.add(subentry_id)

    if existing and importing is not None:
        # During import a marker can refer to a definition later in the document.
        importing.deferred.add(entryID)
    elif existing:
        placeholders = ",".join("?" for _ in existing)
        rows = dictDB.execute(f"select id, doctype, xml from entries where id in ({placeholders})", list(existing)).fetchall()
        for row in rows:
            subentry_id = row["id"]
            doctype = row["doctype"]
            references = existing.pop(subentry_id)
            child = parse(row["xml"])
            stored_definition = child.get(XEMA_DEFINITION_ATTRIBUTE)
            if stored_definition not in config or xema_get_element_name_from_id(xema, stored_definition) != doctype:
                stored_definition = None
            for marker, parent_id in references:
                child_id = xema_get_id_from_element_name(xema, doctype, parent_id)
                if (stored_definition is None or stored_definition == child_id) and is_subentry(config, child, child_id):
                    marker["title"] = get_entry_title(child, configs, xema_element_id=child_id)[0]
                    marker["doctype"] = doctype
                    validSubentryIDs.add(subentry_id)
                else:
                    inline = parse(str(child))
                    inline.attrs.pop("lxnm:id", None)
                    inline.attrs.pop("xmlns:lxnm", None)
                    inline.attrs.pop(XEMA_DEFINITION_ATTRIBUTE, None)
                    marker.replace_with(inline)
        for references in existing.values():
            for marker, _ in references:
                marker.decompose()

    dictDB.execute("delete from sub where parent_id=?", (entryID,))
    if importing is None or not existing:
        dictDB.executemany("insert into sub(parent_id, child_id) values(?,?)",
                           ((entryID, child_id) for child_id in validSubentryIDs))

    # Flag our parents they need an update (in case this is a subentry)
    if not maintenance and importing is None:
        dictDB.execute("update entries set needs_update=1 where needs_update=0 and id in "
                       "(select parent_id from sub where child_id=?)", (entryID,))

def get_entry_doctype(xml: Tag) -> str:
    """Get elementName of the root of the entry xml"""
    return xml.name

def get_text(xml: Tag | EntryText, tagName: Optional[str] = None) -> Optional[str]:
    """
        If tagName and such an element exists: returns the first (non-whitespace) text content of the element.
        if tagName and such an element does not exist: None
        if no tagName: first non-whitespace text content of xml
        if no tagName and no text in the entire xml: None

        Only checks descendants of the xml node.
    """
    if isinstance(xml, EntryText):
        return next(xml.texts(tagName), None) if tagName else xml.first()
    if tagName:
        for el in xml(tagName, string=True):
            textContent = str(el.string.strip()) # convert to python string and trim whitespace (or else whitespace-only strings would leak through.)
            if textContent:
                return textContent
    else:
        for txt in xml.stripped_strings:
            return str(txt)

def get_text_all(xml: Tag | EntryText, tagName: str) -> List[str]:
    """
        If element provided: returns the first (non-whitespace) text content of the element. None is returned if element does not exist or doesn't have any meaningful text anywhere.
        If no element provided: returns the first none-whitespace text content in the document. None is returned if no meaningful text in the entire document.
    """
    if isinstance(xml, EntryText):
        return list(xml.texts(tagName))
    ret: List[str] = []
    for el in xml.findAll(tagName, string=True): # only match those with text content
        textContent = str(el.string.strip()) # convert to python string and trim whitespace (or else whitespace-only strings would leak through.)
        if textContent:
            ret.append(textContent)
    return ret

def get_entry_headword(xml: Tag | EntryText, configs: Configs) -> str:
    """
    Get the entry's headword.
    If no text is found at the element, the first non-whitespace text content of the document will be returned.
    If there is no text at all, a default placeholder is returned.
    """
    config: ConfigTitling = configs["titling"]
    headword_id = config.get("headword")
    headword_element_name = xema_get_element_name_from_id(configs["xema"], headword_id) if headword_id else None
    if headword_element_name and (val := get_text(xml, headword_element_name)):
        return val[0:255]
    elif val := get_text(xml):
        return val[0:255]
    else:
        return DEFAULT_HEADWORD

def get_entry_title(xml: Tag | EntryText, configs: Configs, xema_element_id: str) -> Tuple[str, str]:
    """
    Returns [title as plaintext, title as html]
    This will usually be the headword (and optionally some other things), unless specifically configured by the user (by using advanced mode).
    xema_element_id is required to know whether this element is a subtentry, and to retrieve the correct subentry config if it is. 
    Since subentries have a different schema from the main entry, they may have a different headword element and thus a different title.
    """
    # If this is a subentry and a titling config is present for this subentry type, use it
    if xema_element_id and (headword_xema_id := (configs["subbing"].get(xema_element_id, {}).get("titling") or {}).get("headword")):
        headword_element_name = xema_get_element_name_from_id(configs["xema"], headword_xema_id)
        if headword_element_name and (val := get_text(xml, headword_element_name)):
            headword = val[0:255]
            return headword, f"<span class='headword'>{headword}</span>"
    
    # Fallback to main config
    config: ConfigTitling = configs["titling"]
    titleParts: List[str] = []
    if (formatString := config.get("headwordAnnotationsAdvanced", "")) and config.get("headwordAnnotationsType") == "advanced":
        asHtml: str = formatString  # start with the format string as-is, replace placeholders as we go
        for elementFormatString in re.findall(r"%\([^)]+\)", formatString): # e.g. "%(elementName)"
            elementName = elementFormatString[2:-1] # strip the surrounding syntax %()
            if (text := get_text(xml, elementName)) != None:
                titleParts.append(text)
                asHtml = asHtml.replace(elementFormatString, text)

        if len(titleParts):
            return ' '.join(titleParts), asHtml

    # Run simple mode if we haven't returned yet (because advanced mode either disabled or didn't match anything)
    # start with the headword.
    headword = get_entry_headword(xml, configs)
    for element_id in config.get("headwordAnnotations", []):
        elementName = xema_get_element_name_from_id(configs["xema"], element_id)
        if (text := get_text(xml, elementName)) != None:
            titleParts.append(text)

    stringParts = [headword] + titleParts
    htmlParts = ["<span class='headword'>" + headword + "</span>"] + titleParts
    return ' '.join(stringParts), ' '.join(htmlParts)


def get_entry_sortkey(xml: Tag | EntryText, configs: Configs) -> str:
    """
    Get the entry's sort key as defined by configs.titling.headwordSorting
    Fallbacks are in order:
    - the headword
    - the first text content in the entry
    - a placeholder string
    """
    config = configs["titling"]
    if definition := config.get("headwordSorting"):
        name = xema_get_element_name_from_id(configs["xema"], definition)
        if val := get_text(xml, name):
            return val
    return get_entry_headword(xml, configs)

def get_entry_flag(xml: str | Tag | EntryText, configs: Configs) -> str:
    """Read the flag from an entry, assumes the xml is from the database, and not from the user (and so has no unexpected issues)."""
    if isinstance(xml, str):
        xml = parse(xml)

    flag_element_id = configs.get("flagging", {}).get("flag_element")
    flag_element_name = configs.get("xema", {}).get("elements", {}).get(flag_element_id, {}).get("elementName", flag_element_id)
    flag_text = (get_text(xml, flag_element_name) or "") if flag_element_name else ""
    return flag_text

def find_path_to_element(xema: ConfigXema, current_element_id: str, target_element_id: str) -> Optional[list[str]]:
    """
    Find the (first) path to to the target element.
    The list is returned with the target element at the end. The list contains the xml names of the elements, not their IDS.
    The initial starting point element is NOT returned in the list.
    If any of the encountered elements have no config in the xema it is not considered further.
    """
    seen = set()

    def walk(element_id):
        if element_id in seen:
            return None
        seen.add(element_id)
        for child in xema["elements"].get(element_id, {}).get("children", []):
            child_id = child["name"]
            name = xema_get_element_name_from_id(xema, child_id)
            if child_id == target_element_id:
                return [name]
            if rest := walk(child_id):
                return [name, *rest]
        return None

    return walk(current_element_id)

def create_path_to_element(xml: Tag, path: list[str]) -> Tag:
    """
    Make sure the path exists within the entry, creating missing elements along the way.
    The list should not contain the current xml node, only the descendants to create.
        Ex: create_path_to_element(parse("<a><b></b></a>") , ["b", "c", "d"]) # ensure ./b/c/d exists
            xml is now "<a><b><c><d></d></c></b></a>"
    Returns the final node.
    """
    path = path.copy()
    current_element = xml
     # Find the element closest to the flag in the xml, adding unfound elements as we run across them.
    tagCreator = BeautifulSoup()
    while len(path):
        next_nearest_elementname = path.pop(0)
        if next_element := current_element.findChild(next_nearest_elementname):
            current_element = next_element
        else: # didn't find, add it!
            new_element = tagCreator.new_tag(next_nearest_elementname) # when doing the last entry in the list, the element should be the flag tag itself.
            current_element.append(new_element)
            current_element = new_element
    return current_element

def set_entry_flag(dictDB: Connection, entryID: int, flag: str, configs: Configs, email: str, xml: Optional[Union[Tag, str]] = None) -> Tuple[Optional[Tag], Optional[str]]:
    """
    Update or create the flag element's contents.
    Returns either [xml Tag, None] or [None, feedback], depending on success.
    Load the xml from the database if not passed in. Otherwise it is assumed the xml is from the database (so not just some unprocessed/unvalidated user input).
    Returns the updated xml.
    NOTE: If Tag is passed in - it is modified in place and returned.
    NOTE: XML and flag column in Database are always updated on success.
    NOTE: A history entry is created on success.
    NOTE: You must commit() after doing this.
    """

    # Gather all basic info: parsed xml, flag element name
    flag_element_id: str = configs["flagging"].get("flag_element")
    if not flag_element_id:
        return None, "Cannot set flag as no flags are configured."
    flag_element_name = xema_get_element_name_from_id(configs["xema"], flag_element_id)
    xema: ConfigXema = configs.get("xema", {"elements": {}})

    if not xml: # read xml from db if not supplied
        row = doSql(dictDB, "select id, xml from entries where id=?", (entryID,)).fetchone()
        if not row:
            return None, "Entry not found"
        xml = parse(row["xml"])
    elif isinstance(xml, str):
        xml = parse(xml)

    root_element_id = xema_get_id_from_element_name(xema, xml.name)

    def updateFlag(entryRoot: Tag, the_flag_element: Tag):
        the_flag_element.clear()
        the_flag_element.append(flag) # add the string
        xmlstr = str(entryRoot)
        doSql(dictDB, "update entries set xml=?, flag=? where id=?", (xmlstr, flag, entryID))
        doSql(dictDB, "insert into history(entry_id, action, [when], email, xml, historiography) values(?, ?, ?, ?, ?, ?)", (entryID, "update", str(datetime.datetime.utcnow()), email, xmlstr, json.dumps({})))

        # if the user can search in the flag field (which we just modified), update the search table
        if flag_element_id in configs["searchability"].get("searchableElements", []):
            titleText, titleHtml = get_entry_title(entryRoot, configs, xema_element_id=root_element_id)
            presave_searchables(dictDB, configs, entryRoot, entryID, titleText)

    # Note, we do not check the path to the flag element here.
    # We assume that when it exists, it is valid to use it, and the exact location does not matter very much
    if flag_element := xml.find(flag_element_name):
        updateFlag(xml, flag_element)
        return xml, None

    # flag not present. try and find where we should insert it, and do so.
    # Start looking from the actual entry root instead of schema root,
    # as it is possible this entry does not start at the schema root (such as when this is a subentry).
    path_to_flag = find_path_to_element(xema, root_element_id, flag_element_id) or [flag_element_name] # if we can't find a path, add the flag directly below the root.
    flag_element = create_path_to_element(xml, path_to_flag)
    updateFlag(xml, flag_element)
    return xml, None


def presave_searchables(dictDB: Connection, configs: Configs, entryXml: Tag, entryID: int, entryTitleText: str):
    dictDB.execute("delete from searchables where entry_id=?", (entryID,))
    dictDB.executemany(INSERT_SEARCHABLE, entry_searchables(configs, entryXml, entryID, entryTitleText))


INSERT_SEARCHABLE = "insert into searchables(entry_id, txt, level) values(?, ?, ?)"


def entry_searchables(configs: Configs, entryXml: Tag | EntryText, entryID: int, entryTitleText: str):
    # Level 2 searchables: headword, plus everything in config - do this first so we can check we don't have duplicates.
    searchablesLevel2: Set[str] = set()
    searchablesLevel2.add(get_entry_headword(entryXml, configs))
    for element_id in configs["searchability"].get("searchableElements", []):
        element_name = xema_get_element_name_from_id(configs["xema"], element_id)
        for txt in get_text_all(entryXml, element_name):
            searchablesLevel2.add(txt)

    # Level 1: title and title lowercase - insofar as those are not in level 2
    searchablesLevel1: set[str] = set()
    if entryTitleText not in searchablesLevel2:
        searchablesLevel1.add(entryTitleText)
    if (entryTitleTextLower := entryTitleText.lower()) not in searchablesLevel2:
        searchablesLevel1.add(entryTitleTextLower)

    return list(
        itertools.chain(
            zip(itertools.repeat(entryID), searchablesLevel1, itertools.repeat(1)),
            zip(itertools.repeat(entryID), searchablesLevel2, itertools.repeat(2))
        )
    )


def split_template_string(template: str) -> list[str]:
    "Extract and return the templates from a template-string like %(some-element)"
    return re.findall(r"%\([^)]+\)", template) # pre-process

def eval_template_string(entry: Tag, current_element: Tag, template: str, split_template: Optional[list[str]] = None) -> str:
    """Replace templates %(some-element) and %(@some-attribute) with their text values.
        Unmatched templates are preserved.
        Elements are first matched inside current_element, and if that fails, on the entire entry.

    Args:
        entry (Tag): the entry, used as fallback when template string refers to an element that can't be found in/below the current_element
        current_element (Tag): element for which to evaluate the template
        template (str): complete template string
        split_template (list[str]): speedup for when calling this function in a loop, the pre-extracted templates from the string.

    Returns:
        str: the template string with templates replaced by their values
    """

    if not split_template:
        split_template = split_template_string(template)

    for pattern in split_template:
        if pattern[2] == '@': # if the pattern is %(@some-attribute), extract it
            attributeName = pattern[3:-1]
            text = current_element.attrs.get(attributeName) or entry.attrs.get(attributeName)
        else: # pattern is %(some_element)
            elementName = pattern[2:-1]
            text = get_text(current_element, elementName) or get_text(entry, elementName) # use descendants of the link element first, if that fails try entire entry
        if text:
            template = template.replace(pattern, text)
    return template

def presave_linkables(dictDB: Connection, configs: Configs, entryXml: Tag, entryID: int):
    """
    Purge outdated linkables, find new linkables, make linkables database up-to-date for this entry.
    Entry is not saved yet, only its xml is changed.

    A linkable is just an element with an @lxnm:linkable attribute.
    The frontend uses these to generate links to other places when displaying an entry.
    The backend is not concerned with this further, we just keep them consistent with the config and save them in the db for the frontend.

    entryID is passed in to prevent repeatitive database lookups during processing of (new or currently saving) entries.
    """

    xema = configs.get("xema", {"elements": {}})
    config_links = configs.get("links", {})

    # First remove all linkables, so we don't keep any stale entries around either in the entry or the database.
    doSql(dictDB, "delete from linkables where entry_id=?", (entryID,))
    for linkable in entryXml.findAll(attrs = {"lxnm:linkable": True}): # match all with linkable attribute
        del linkable.attrs["lxnm:linkable"]

    ret: List[Tuple[int, str, str, str]] = []
    for linkref in config_links.values():
        if type(linkref) is str:
            continue
        linkElement = xema_get_element_name_from_id(xema, linkref["linkElement"])

        identifierEscapes = split_template_string(linkref["identifier"]) # pre-process
        previewEscapes = split_template_string(linkref["preview"])
        for el in entryXml.findAll(linkElement):
            identifier = eval_template_string(entryXml, el, linkref["identifier"], identifierEscapes)
            preview = eval_template_string(entryXml, el, linkref["preview"], previewEscapes)
            el.attrs["lxnm:linkable"] = identifier
            ret.append((entryID, identifier, linkElement, preview))

    if len(ret):
        dictDB.executemany("insert into linkables(entry_id, txt, element, preview) values(?,?,?,?)", ret)

def get_next_autonumber_value(dictDB: Connection, element: str, target: Optional[str]) -> Optional[int]:
    """Scan all entries for values in the element or the attribute on the element (if supplied), returning the highest found number + 1

    Args:
        dictDB (Connection): the dictionary
        element (str): name of the element to scan
        target (Optional[str]): name of the actual container element or attribute, attribute should be prefixed with 'a'. See ConfigAutoNumber["target"].
    """

    target_is_attribute = False
    if target and target.startswith("@"):
        target_is_attribute = True
        target = target[1:]

    # """Get the next unused integer for an autonumber configuration."""
    highest = -1
    for e in dictDB.execute("select xml from entries"):
        entry = parse(e["xml"])
        for el in ([entry] + entry.findAll(element)) if entry.name == element else entry.findAll(element):
            existing_value = el.attrs.get(target) if target_is_attribute else get_text(el, target)
            if existing_value:
                try:
                    i = int(existing_value)
                    highest = i if i > highest else highest
                except:
                    pass
    highest += 1 # return NEXT number
    configs = readDictConfigs(dictDB)
    # since this is a long operation - just save it now.
    config = configs.get("autonumbering", {})
    if elementConf := config.get(element):
        elementConf["number_next"] = highest
        dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(config), "autonumbering"))

    return highest

def presave_autonumbering(dictDB: Connection, configs: Configs, entry: Tag, isAutoApplying: bool = True) -> bool:
    """Add automatically generated IDS/numbers to elements/attributes in the entry according to the config.
    If the next ID is persistent, the config is then written to the database with the updating running nummer.

    Args:
        dictDB (Connection): database
        config (list[ConfigAutoNumbering]): autonumbers to apply
        isNewEntry (bool): Is this a new entry, or an update to an existing entry? Used to skip refreshing numeric IDs on existing entries.
        isAutoApplying (bool): Are we autonumbering in the context of a user that pressed "autonumber my dictionary" or are we just processing a single entry during saving?

    Returns:
        true if the xml was changed
    """
    xema = configs["xema"]
    autonumbering = configs.get("autonumbering", {})

    touched_global_number = False
    touched_entry = False
    for c in autonumbering.values():
        # Be a little smart about this:
        # Only overwrite values when running auto_apply on a new entry, or when doing a manual run with overwrite true
        if not c.get("auto_apply") and isAutoApplying:
            continue

        # setup
        value_type = c.get("type", "number") # number or string
        element_to_number = xema_get_element_name_from_id(xema, c.get("element", ""))
        target = c.get("target") or None # Note: keep None if not valid, or get_text call later fails because it will look for empty string element or something.
        target_is_attribute = False
        if target and target.startswith("@"):
            target_is_attribute = True
            target = target[1:]

        if not element_to_number:
            continue

        if value_type == "number":
            next_number = int(c.get("number_next", 0)) if c.get("number_globally") else 0
            template = None
            template_parts = None
        else: # value_type == "string":
            next_number = 0
            template = c.get("string_template")
            template_parts = split_template_string(template) if template else None
            if not template_parts: # template string is empty, missing, or contains nothing to evaluate; skip.
                continue

        for el in ([entry] + entry.findAll(element_to_number)) if entry.name == element_to_number else entry.findAll(element_to_number):
            existing_value = el.attrs.get(target) if target_is_attribute else get_text(el, target)
            write_new_value = not existing_value or c.get("overwrite_existing")

            # Exception to the rule:
            # When in numeric mode, and numbers are globally unique, and we're auto-applying: don't overwrite
            # Doing that would cause new numbers to be assigned every time an entry is saved or otherwise touched.
            # Which would be completely useless from an ID standpoint, and also cause the numbers to grow rather quickly..
            # So only overwrite existing global numbers if not isAutoApplying
            # Local numbers are fine to overwrite, since they are usually the same, unless the entry added or removed the elements to count.
            # And in that case you probably DO want the ids to auto-update since they're more local index numbers instead of actual idenfitiers.
            if value_type == "number" and c.get("number_globally") and existing_value and isAutoApplying:
                write_new_value = False

            if not write_new_value:
                continue

            if value_type == "number":
                value = str(next_number)
                next_number += 1
            else:
                value = eval_template_string(entry, el, template, template_parts)

            touched_entry = True
            if target_is_attribute:
                el.attrs[target] = value
            elif target:
                targetEl = el.find(target) or create_path_to_element(el, [target])
                targetEl.clear()
                targetEl.append(value)
            else:
                el.clear()
                el.append(value)

        # After writing the values, save the current number so we can continue in later entries
        if value_type == "number" and c.get("number_globally"):
            c["number_next"] = next_number
            touched_global_number = True

    if touched_global_number:
        dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(autonumbering), "autonumbering"))

    return touched_entry


def same_imported_entry(xema: ConfigXema, definition_id: str, stored: Tag, incoming: Tag,
                        inherited_preserve: bool) -> bool:
    """Compare duplicate definitions without changing either XML tree."""
    def has_text(node: Tag) -> bool:
        return any(type(child) in (NavigableString, CData) and child.strip(" \t\r\n")
                   for child in node.contents)

    def significant_whitespace(left: Tag, right: Tag, element_id: str, preserve_space: bool) -> bool:
        definition = xema["elements"].get(element_id)
        if definition is not None and xema_get_element_name_from_id(xema, element_id) == left.name:
            # Match Xematron's hasText; an omitted filling defaults to child elements.
            return definition.get("filling") in ("inl", "txt", "lst", "med")
        return preserve_space or has_text(left) or has_text(right)

    def children(node: Tag, preserve: bool):
        # Expat may split the same run of text differently across parses.
        for is_text, group in itertools.groupby(node.contents, key=lambda child: type(child) is NavigableString):
            if not is_text:
                yield from group
            else:
                text = "".join(group)
                if preserve or text.strip(" \t\r\n"):
                    yield text

    pending = [(stored, incoming, definition_id, inherited_preserve)]
    while pending:
        left, right, element_id, preserve_space = pending.pop()
        if left.name != right.name or left.attrs != right.attrs:
            return False
        preserve_space = preserve_space or left.get("xml:space") == "preserve"
        preserve = significant_whitespace(left, right, element_id, preserve_space)
        for a, b in itertools.zip_longest(children(left, preserve), children(right, preserve)):
            if type(a) is not type(b):
                return False
            if isinstance(a, Tag):
                child_id = xema_get_id_from_element_name(xema, a.name, element_id)
                pending.append((a, b, child_id, preserve_space))
            elif a != b:
                return False
    return True


def createEntry(dictDB: Connection, configs: Configs, xml: Union[str, Tag], email: str, id: Optional[int] = None,
                *, commit: bool = True, xema_element_id: Optional[str] = None,
                maintenance: bool = False, importing: ImportEntries | None = None,
                inherited_preserve: bool = False) -> Union[
    Tuple[int, Tag, Literal[True], Optional[Any]],
    Tuple[Optional[int], Optional[Tag], Literal[False], Any]
]:
    """
    Create or re-index an entry, ensuring the xml is conformant and the database is up to date.
    Returns in order: id, parsed xml, success (true/false), feedback as JSON object {"type": string, "info": string|int} when duplicate entry or otherwise error.

    When ID is passed, it is used instead of whatever ID is contained in the xml. If no id is passed, extract the id from the xml, or, failing that, auto-assign an ID.
    """

    if isinstance(xml, str) or xml is None:
        try:
            xml = parse(xml)
        except:
            return id, None, False, {"type": "savingFailed", "info": "Invalid XML."}

    fixup_namespaces(xml)

    # Specific order: reserve ID in the database, then extract subentries
    # So that any element matching after this does not go into subentries
    doctype = get_entry_doctype(xml)
    id, isNewEntry = get_entry_id(xml, dictDB, id)
    if importing is not None and not xema_element_id and XEMA_DEFINITION_ATTRIBUTE not in xml.attrs:
        alias = importing.aliases.get(id)
        if alias and xema_get_element_name_from_id(configs["xema"], alias) == doctype:
            xema_element_id = alias
    definition_id = xema_element_id or entry_schema_id(configs, xml)
    old_xml = None
    old_entry = None
    if not isNewEntry and not xema_element_id and XEMA_DEFINITION_ATTRIBUTE not in xml.attrs:
        old_xml = dictDB.execute("select xml from entries where id=?", (id,)).fetchone()["xml"]
        if old_xml and XEMA_DEFINITION_ATTRIBUTE in old_xml:
            old_entry = parse(old_xml)
            if old_entry.name == doctype:
                definition_id = entry_schema_id(configs, old_entry)
    if definition_id != doctype and definition_id in configs["subbing"]:
        xml[XEMA_DEFINITION_ATTRIBUTE] = definition_id
    else:
        xml.attrs.pop(XEMA_DEFINITION_ATTRIBUTE, None)
    presave_subentries(dictDB, configs, xml, id, email, definition_id, maintenance=maintenance,
                       importing=importing, inherited_preserve=inherited_preserve)
    if importing is None or not importing.archival:
        presave_autonumbering(dictDB, configs, xml, isAutoApplying=True)
    titleText, titleHtml = get_entry_title(xml, configs, definition_id)
    sortKey = get_entry_sortkey(xml, configs)
    flag = get_entry_flag(xml, configs)

    presave_linkables(dictDB, configs, xml, id)
    # Create/update the entry, save history
    xmlstr = str(xml)
    if importing is not None:
        if id in importing.defined:
            if old_xml is None:
                old_xml = dictDB.execute("select xml from entries where id=?", (id,)).fetchone()[0]
            if xmlstr != old_xml and not same_imported_entry(
                configs["xema"], definition_id, old_entry if old_entry is not None else parse(old_xml), xml,
                inherited_preserve or importing.defined[id],
            ):
                raise ValueError(f"Conflicting definitions for entry {id} in the same XML document.")
            return id, xml, True, None
        importing.defined[id] = inherited_preserve
    presave_searchables(dictDB, configs, xml, id, titleText)
    doSql(dictDB, "update entries set doctype=?, xml=?, title=?, sortkey=?, flag=?, needs_update=0 where id=?", (doctype, xmlstr, titleHtml, sortKey, flag, id))
    if not maintenance:
        doSql(dictDB, "insert into history(entry_id, action, [when], email, xml, historiography) values(?, ?, ?, ?, ?, ?)", (id, "create" if isNewEntry else "update", str(datetime.datetime.now(datetime.timezone.utc)), email, xmlstr, "{}"))

    # Only an interactive save needs feedback about another entry.
    r = dictDB.execute("select id from entries where title = ? and id <> ? limit 1", (titleText, id)).fetchone() if commit else None
    if commit:
        dictDB.commit()
    feedback = {"type": "saveFeedbackHeadwordExists", "info": r["id"]} if r else None

    return id, xml, True, feedback

def generateKey(size: int=32):
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(size))

def generateDictId(size: int=8):
    return ''.join(random.choice("abcdefghijkmnpqrstuvwxy23456789") for _ in range(size))

def login(email: str, password: str):
    if siteconfig["readonly"]:
        return {"success": False}
    with getMainDB() as conn:
        passhash = hashlib.sha1(password.encode("utf-8")).hexdigest()
        c = conn.execute("select email, consent from users where email=? and passwordHash=?", (email.lower(), passhash))
        user = c.fetchone()
        if not user:
            return {"success": False}
        key = generateKey()
        now = datetime.datetime.utcnow()
        conn.execute("update users set sessionKey=?, sessionLast=? where email=?", (key, now, user["email"]))
        conn.commit()
        return {"success": True, "email": user["email"], "key": key, "consent": user["consent"] == 1}

def logout(user: User):
    with getMainDB() as conn:
        conn.execute("update users set sessionKey='', sessionLast='' where email=?", (user["email"],))
        conn.commit()
        return True

def sendSignupToken(email: str, remoteip: str):
    if siteconfig["readonly"] or (email.lower() == INITIAL_ADMIN and INITIAL_ADMIN in siteconfig["admins"]):
        return False

    with getMainDB() as conn:
        if conn.execute("select email from users where email=?", (email.lower(),)).fetchone():
            return False # user already exists, cannot register again

    token = secrets.token_hex()
    tokenurl = siteconfig["clientUrl"] + "#/createaccount/" + token
    expireDate = datetime.datetime.now() + datetime.timedelta(days=2)
    mailSubject = "Lexonomy signup"
    mailText = "Dear Lexonomy user,\n\n"
    mailText += "Somebody (hopefully you, from the address "+remoteip+") requested to create a new Lexonomy account. Please follow the link below to create your account:\n\n"
    mailText += tokenurl + "\n\n"
    mailText += "For security reasons this link is only valid for two days (until "+expireDate.isoformat()+"). If you did not request an account, you can safely ignore this message. \n\n"
    mailText += "Yours,\nThe Lexonomy team"
    conn.execute("insert into register_tokens (email, requestAddress, token, expiration) values (?, ?, ?, ?)", (email, remoteip, token, expireDate))
    conn.commit()
    sendmail(email, mailSubject, mailText)
    return True


def sendToken(email: str, remoteip: str):
    if siteconfig["readonly"]:
        return False
    with getMainDB() as conn:
        if not conn.execute("select email from users where email=?", (email.lower(),)).fetchone():
            return False # user does not exist, cannot reset password

    token = secrets.token_hex()
    tokenurl = siteconfig["clientUrl"] + "#/recoverpwd/" + token
    expireDate = datetime.datetime.now() + datetime.timedelta(days=2)
    mailSubject = "Lexonomy password reset"
    mailText = "Dear Lexonomy user,\n\n"
    mailText += "Somebody (hopefully you, from the address "+remoteip+") requested a new password for the Lexonomy account "+email+". You can reset your password by clicking the link below:\n\n";
    mailText += tokenurl + "\n\n"
    mailText += "For security reasons this link is only valid for two days (until "+expireDate.isoformat()+"). If you did not request a password reset, you can safely ignore this message. \n\n"
    mailText += "Yours,\nThe Lexonomy team"
    conn.execute("insert into recovery_tokens (email, requestAddress, token, expiration) values (?, ?, ?, ?)", (email, remoteip, token, expireDate))
    conn.commit()
    sendmail(email, mailSubject, mailText)
    return True

def verifyToken(token: str, tokenType: Literal["recovery", "register"]):
    if tokenType not in ("recovery", "register"):
        return False
    with getMainDB() as conn:
        row = conn.execute(
            f"select 1 from {tokenType}_tokens where token=? and expiration>=datetime('now') and usedDate is null",
            (token,),
        ).fetchone()
        return row is not None

def createAccount(token: str, password: str, remoteip: str):
    with getMainDB() as conn:
        c = conn.execute("select * from register_tokens where token=? and expiration>=datetime('now') and usedDate is null", (token,))
        row = c.fetchone()
        if row and row["email"].lower() == INITIAL_ADMIN and INITIAL_ADMIN in siteconfig["admins"]:
            return False
        if row:
            c2 = conn.execute("select * from users where email=?", (row["email"],))
            row2 = c2.fetchone()
            if not row2:
                passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
                conn.execute("insert into users (email,passwordHash) values (?,?)", (row["email"], passhash))
                conn.execute("update register_tokens set usedDate=datetime('now'), usedAddress=? where token=?", (remoteip, token))
                conn.commit()
                # notify admins?
                if siteconfig.get('notifyRegister') == True:
                    mailSubject = "Lexonomy, new user registered"
                    mailText = "Hi,\n\n"
                    mailText += "new user registered to Lexonomy at " + siteconfig["clientUrl"] + " :\n\n"
                    mailText += "  " + row["email"]
                    mailText += "\n\nYours,\nThe Lexonomy team"
                    for adminMail in siteconfig["admins"]:
                        sendmail(adminMail, mailSubject, mailText)
                return True
            else:
                return False
        else:
            return False

def resetPwd(token: str, password: str, remoteip: str):
    with getMainDB() as conn:
        c = conn.execute("select * from recovery_tokens where token=? and expiration>=datetime('now') and usedDate is null", (token,))
        row = c.fetchone()
        if row:
            passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
            conn.execute("update users set passwordHash=? where email=?", (passhash, row["email"]))
            conn.execute("update recovery_tokens set usedDate=datetime('now'), usedAddress=? where token=?", (remoteip, token))
            conn.commit()
            return True
        else:
            return False

def setConsent(email: str, consent: bool):
    with getMainDB() as conn:
        conn.execute("update users set consent=? where email=?", (consent, email))
        conn.commit()
        return True

def changePwd(email: str, password: str):
    with getMainDB() as conn:
        passhash = hashlib.sha1(password.encode("utf-8")).hexdigest();
        conn.execute("update users set passwordHash=? where email=?", (passhash, email))
        conn.commit()
        return True

def dictExists(dictID: str) -> bool:
    return os.path.isfile(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite"))

def suggestDictId() -> str:
    dictid = generateDictId()
    while dictid in prohibitedDictIDs or dictExists(dictid):
        dictid = generateDictId()
    return dictid

def makeDict(dictID: str, template: str, title: str, blurb: str, email: str):
    if title == "":
        title = "?"
    if dictID in prohibitedDictIDs or dictExists(dictID):
        return False
    if not template:
        template = "blank"
    if not template.startswith("/"):
        template = os.path.join(API_DIR, "dictTemplates", template + ".sqlite.schema")
    #init db schema
    schema = open(template, 'r').read()
    with sqlite3.connect(os.path.join(siteconfig["dataDir"], "dicts", dictID + ".sqlite")) as conn:
        conn.executescript(schema)
        conn.commit()
    #update dictionary info
    users = {email: {"canEdit": True, "canConfig": True, "canDownload": True, "canUpload": True}}
    with getDB(dictID) as dictDB:    
        c = dictDB.execute("SELECT count(*) AS total FROM configs WHERE id='users'")
        r = c.fetchone()
        if r['total'] == 0:
            dictDB.execute("INSERT INTO configs (id, json) VALUES (?, ?)", ("users", json.dumps(users)))
        else:
            dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(users), "users"))
        ident = {"title": title, "blurb": blurb}
        c = dictDB.execute("SELECT count(*) AS total FROM configs WHERE id='ident'")
        r = c.fetchone()
        if r['total'] == 0:
            dictDB.execute("INSERT INTO configs (id, json) VALUES (?, ?)", ("ident", json.dumps(ident)))
        else:
            dictDB.execute("UPDATE configs SET json=? WHERE id=?", (json.dumps(ident), "ident"))
        dictDB.commit()
        attachDict(dictDB, dictID)
        return True

def attachDict(dictDB: Connection, dictID: str):
    configs = readDictConfigs(dictDB)
    with getMainDB() as conn:
        conn.execute("delete from dicts where id=?", (dictID,))
        conn.execute("delete from user_dict where dict_id=?", (dictID,))
        title = configs["ident"]["title"]
        conn.execute("insert into dicts(id, title) values (?, ?)", (dictID, title))
        for email in configs["users"]:
            conn.execute("insert into user_dict(dict_id, user_email) values (?, ?)", (dictID, email.lower()))
        conn.commit()

def cloneDict(dictID: str, email: str):
    newID = suggestDictId()
    for ext in [".sqlite", ".sqlite-wal", ".sqlite-shm"]:
        old_file = os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ext)
        new_file = os.path.join(siteconfig["dataDir"], "dicts", newID + ext)
        if os.path.exists(old_file):
            shutil.copy(old_file, new_file)

    with getDB(newID) as newDB:
        res = newDB.execute("select json from configs where id='ident'")
        row = res.fetchone()
        ident = {"title": "?", "blurb": "?"}
        if row:
            ident = json.loads(row["json"])
            ident["title"] = "Clone of " + ident["title"]
        newDB.execute("update configs set json=? where id='ident'", (json.dumps(ident),))
        newDB.commit()
        attachDict(newDB, newID)
        return {"success": True, "dictID": newID, "title": ident["title"]}

def destroyDict(dictID: str):
    with getMainDB() as conn:
        conn.execute("delete from dicts where id=?", (dictID,))
        conn.execute("delete from user_dict where dict_id=?", (dictID,))
        conn.commit()
        os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite"))
        if os.path.exists(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-wal")):
            os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-wal"))
        if os.path.exists(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-shm")):
            os.remove(os.path.join(siteconfig["dataDir"], "dicts/" + dictID + ".sqlite-shm"))
        return True

def moveDict(oldID: str, newID: str):
    # Only allow IDs with word, space, underscore, or dash characters (including non-western letters)
    if not re.match(r'^[\w\s\-]+$', newID, re.UNICODE) or newID in prohibitedDictIDs or dictExists(newID):
        print(f"moveDict: Cannot move dict: '{newID}' contains invalid characters, already exists, or is prohibited.")
        return False
    
    # Perform an operation that will fail if the database is in use, to ensure it is not locked.
    # Performing a checkpoint also nicely reduces the size of the (sometimes quite large) WAL file.
    with getDB(oldID) as db:
        try:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            print(f"moveDict: Failed to commit checkpoint for {oldID}. The database may be in use.")
            return False

    import shutil

    # NOTE: USE COPY + DELETE, DO NOT USE MOVE/RENAME
    # There is an issue with bind mounts in docker where using os.rename() or shutil.move() causes a strange state
    # where the file is moved on the host, but the container still sees the old file.
    # The only way to reliably move files in this case seems to be to copy them and then delete the old ones.
    dicts_dir = os.path.abspath(os.path.join(siteconfig["dataDir"], "dicts"))
    files = [
        (os.path.join(dicts_dir, oldID + ext), 
        os.path.join(dicts_dir, newID + ext)) 
        for ext in [".sqlite", ".sqlite-wal", ".sqlite-shm"]]
    for old_file, new_file in files:
        if os.path.exists(old_file):
            try:
                shutil.copy2(old_file, new_file)
            except Exception as e:
                print(f"moveDict: Failed to copy {old_file} to {new_file}: {e}")
                return False

    # Attach the new dict and destroy the old one
    with getDB(newID) as newDB:
        attachDict(newDB, newID)
    destroyDict(oldID)
    
    return True

class DictInfo(TypedDict):
    id: str
    title: str
    hasLinks: bool
    lang: str
    currentUserCanEdit: NotRequired[bool]
    currentUserCanDelete: NotRequired[bool]
    size: NotRequired[int]
    broken: NotRequired[bool]
    author: NotRequired[str]
    licence: NotRequired[str]
    favorite: NotRequired[bool]

def getDictsByUser(email: str) -> list[DictInfo]:
    dicts: List[DictInfo] = []
    email = str(email).lower()
    with getMainDB() as conn:
        favs = []
        c = conn.execute("SELECT * FROM dict_fav WHERE user_email=?", (email,))
        for r in c.fetchall():
            favs.append(r['dict_id'])
        c = conn.execute("SELECT DISTINCT d.id, d.title FROM dicts AS d INNER JOIN user_dict AS ud ON ud.dict_id=d.id WHERE ud.user_email=? OR d.id IN (SELECT dict_id FROM dict_fav WHERE user_email=?) ORDER BY d.title", (email, email))
        for r in c.fetchall():
            info: DictInfo = {"id": r["id"], "title": r["title"], "hasLinks": False, "lang": "", "favorite": False}
            try:
                with getDB(r["id"]) as dictDB:
                    cc = dictDB.execute("select count(*) as total from entries")
                    info["size"] = cc.fetchone()["total"]
                    configs = readDictConfigs(dictDB)
                    if configs["users"][email] and configs["users"][email]["canEdit"]:
                        info["currentUserCanEdit"] = True
                    if configs["users"][email] and configs["users"][email]["canConfig"]:
                        info["currentUserCanDelete"] = True
                    if configs["links"] and len(configs["links"])>0:
                        info["hasLinks"] = True
                    if configs["ident"] and configs["ident"]["lang"]:
                        info["lang"] = configs["ident"]["lang"]
                    if r["id"] in favs:
                        info["favorite"] = True
            except:
                info["broken"] = True
            dicts.append(info)
        return dicts

def getPublicDicts() -> list[DictInfo]:
    with getMainDB() as conn:
        c = conn.execute("select * from dicts order by title")
        dicts: List[DictInfo] = []
        for r in c.fetchall():
            try: 
                with getDB(r["id"]) as dictDB:
                    configs = readDictConfigs(dictDB)
                    if configs["publico"]["public"]:
                        cc = dictDB.execute("select count(*) as total from entries")
                        size = cc.fetchone()["total"]
                        dictinfo: DictInfo = {"id": r["id"], "title": r["title"], "author": "", "lang": configs["ident"].get("lang"), "licence": configs["publico"]["licence"], "size": size, "hasLinks": False}
                        if len(list(configs["users"].keys())) > 0:
                            dictinfo["author"] = re.sub(r"@.*","@...", list(configs["users"].keys())[0])
                        dicts.append(dictinfo)
            except:
                continue
        return dicts

def listUsers(searchtext: str, howmany: int) -> UserList:
    with getMainDB() as conn:
        c = conn.execute("select * from users where email like ? order by email limit ?", ("%"+searchtext+"%", howmany))
        users: List[ListedUser] = []
        for r in c.fetchall():
            users.append({"id": r["email"], "title": r["email"]})
        c = conn.execute("select count(*) as total from users where email like ?", ("%"+searchtext+"%", ))
        r = c.fetchone()
        total = r["total"]
        return {"entries":users, "total": total}

# Admin functionality
def createUser(xml: str):
    from lxml import etree as ET
    root = ET.fromstring(xml)
    email = root.attrib["email"]
    passhash = hashlib.sha1(root.attrib["password"].encode("utf-8")).hexdigest();
    with getMainDB() as conn:
        conn.execute("insert into users(email, passwordHash) values(?, ?)", (email.lower(), passhash))
        conn.commit()
        return {"entryID": email, "adjustedXml": readUser(email)["xml"]}

def updateUser(email, xml):
    from lxml import etree as ET
    root = ET.fromstring(xml)
    if root.attrib['password']:
        passhash = hashlib.sha1(root.attrib["password"].encode("utf-8")).hexdigest();
        with getMainDB() as conn:
            conn.execute("update users set passwordHash=? where email=?", (passhash, email.lower()))
            conn.commit()
    return readUser(email)

def deleteUser(email: str):
    with getMainDB() as conn:
        conn.execute("delete from users where email=?", (email.lower(),))
        conn.commit()
    return True

def readUser(email: str):
    with getMainDB() as conn:
        c = conn.execute("select * from users where email=?", (email.lower(), ))
        r = c.fetchone()
    if r:
        if r["sessionLast"]:
            xml =  "<user lastSeen='"+r["sessionLast"]+"'>"
        else:
            xml =  "<user>"
        c2 = conn.execute("select d.id, d.title from user_dict as ud inner join dicts as d on d.id=ud.dict_id  where ud.user_email=? order by d.title", (r["email"], ))
        for r2 in c2.fetchall():
            xml += "<dict id='" + r2["id"] + "' title='" + clean4xml(r2["title"]) + "'/>"
        xml += "</user>"
        return {"email": r["email"], "xml": xml}
    else:
        return {"email":"", "xml":""}

def listDicts(searchtext, howmany):
    with getMainDB() as conn:
        c = conn.execute("select * from dicts where id like ? or title like ? order by id limit ?", ("%"+searchtext+"%", "%"+searchtext+"%", howmany))
        dicts = []
        for r in c.fetchall():
            dicts.append({"id": r["id"], "title": r["title"]})
        c = conn.execute("select count(*) as total from dicts where id like ? or title like ?", ("%"+searchtext+"%", "%"+searchtext+"%"))
        r = c.fetchone()
        total = r["total"]
        return {"entries": dicts, "total": total}

def readDict(dictId):
    with getMainDB() as conn:
        c = conn.execute("select * from dicts where id=?", (dictId, ))
        r = c.fetchone()
        if r:
            xml =  "<dict id='"+clean4xml(r["id"])+"' title='"+clean4xml(r["title"])+"'>"
            c2 = conn.execute("select u.email from user_dict as ud inner join users as u on u.email=ud.user_email where ud.dict_id=? order by u.email", (r["id"], ))
            for r2 in c2.fetchall():
                xml += "<user email='" + r2["email"] + "'/>"
            xml += "</dict>"
            return {"id": r["id"], "xml": xml}
        else:
            return {"id":"", "xml":""}

def clean4xml(text: str) -> str:
    "Escape the xml"
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("'", "&apos;").replace("<", "&lt;").replace(">", "&gt;");

def markdown_text(text: str) -> str:
    "Render markdown as html"
    return markdown.markdown(text).replace("<a href=\"http", "<a target=\"_blank\" href=\"http")

def exportEntryXml(dictDB: Connection, dictID: str, entryID: int, configs: Configs, baseUrl: str):
    c = dictDB.execute("select * from entries where id=?", (entryID,))
    row = c.fetchone()
    if row:
        xml = row["xml"]
        attribs = " this=\"" + baseUrl + dictID + "/" + str(row["id"]) + ".xml\""
        c2 = dictDB.execute("select e1.id, e1.title from entries as e1 where e1.sortkey<(select sortkey from entries where id=?) order by e1.sortkey desc limit 1", (entryID, ))
        r2 = c2.fetchone()
        if r2:
            attribs += " previous=\"" + baseUrl + dictID + "/" + str(r2["id"]) + ".xml\""
        c2 = dictDB.execute("select e1.id, e1.title from entries as e1 where e1.sortkey>(select sortkey from entries where id=?) order by e1.sortkey asc limit 1", (entryID, ))
        r2 = c2.fetchone()
        if r2:
            attribs += " next=\"" + baseUrl + dictID + "/" + str(r2["id"]) + ".xml\""
        xml = "<lexonomy" + attribs + ">" + xml + "</lexonomy>"
        return {"entryID": row["id"], "xml": xml}
    else:
        return {"entryID": 0, "xml": ""}

def resolveSubentries(dictDB: Connection, xml: str | Tag, ancestors: frozenset[int] = frozenset()) -> Tag:
    "Recursively replace subentry references (<lxnm:subentryParent>) with their contents."
    if type(xml) is str:
        xml = parse(xml)
    subs = xml.find_all("lxnm:subentryParent")
    for sub in subs:
        subentryID = int(sub.attrs["id"])
        if subentryID in ancestors:
            continue
        r = dictDB.execute("select * from entries where id = ?", (subentryID, )).fetchone()
        if r:
            sub.replace_with(resolveSubentries(dictDB, r["xml"], ancestors | {subentryID}))

    return xml

def export(dictID: str, dictDB: Connection, configs: Configs, clean: bool = True) -> Iterable[str]:
    """Stream the original XML layout and write each archival entry definition once."""
    rootname = re.sub(r"\s+", "-", dictID).lstrip("0123456789-") or "lexonomy"
    try:
        ParserCreate(namespace_separator=" ").Parse(f"<{rootname}/>", True)
    except ExpatError:
        rootname = "lexonomy"
    xsl = configs.get("download", {}).get("xslt")
    run_xslt = get_xslt_transformer(xsl) if clean and xsl else None
    flag_id = configs["flagging"].get("flag_element") if clean else None
    flag = xema_get_element_name_from_id(configs["xema"], flag_id) if flag_id else None

    return export_document(dictDB, rootname, clean=clean, flag=flag, transform=run_xslt)


def readNabesByEntryID(dictDB: Connection, dictID: str, entryID: int, configs: Configs):
    """In a list of all entries of the root type, return the nearby entries of the target.
        E.G. id of entry "water" is inserted: return 8 previous and 15 following entries next to entry "water".
    """
    nabes: List[SortableEntry] = []
    c = dictDB.execute("select id, sortkey, from entries where doctype=? ", (configs["xema"]["root"],))
    for r in c.fetchall():
        nabes.append({"id": r["id"], "sortkey": r["sortkey"]})

    sortEntries(configs, nabes)

    #select before/after entries
    i = 0
    for n in nabes:
        if n["id"] == -1:
            break
        i += 1

    # Return the surrounding entries, excluding the target entry
    return readEntries(dictDB, configs, nabes[i-8: i] + nabes[i+1:i+15], xml=False)


def readRandoms(dictDB: Connection):
    configs = readDictConfigs(dictDB)
    limit = 75
    xema = configs["xema"]
    doctype = xema_get_element_name_from_id(xema, xema["root"])
    c = dictDB.execute("select id, sortkey from entries where doctype=? order by random() limit ?", (doctype, limit))
    ids_and_sortkeys: List[SortableEntry] = []
    for r in c.fetchall():
        ids_and_sortkeys.append({"id": r["id"], "sortkey": r["sortkey"]})

    return {
        "entries": readEntries(dictDB, configs, ids_and_sortkeys, titlePlain=True),
        "more": dictDB.execute("select count(*) as total from entries where doctype=?", (doctype,)).fetchone()["total"] > limit
    }

def readRandomOne(dictDB: Connection, configs: Configs) -> EntryFromDatabase:
    xema = configs["xema"]
    doctype = xema_get_element_name_from_id(xema, xema["root"])
    row = dictDB.execute("select id from entries where doctype=? order by random() limit 1", (doctype,)).fetchone()
    entries = readEntries(dictDB, configs, row["id"], xml=True) if row else []
    return entries[0] if len(entries) > 0 else {
        "flag": "",
        "id": 0,
        "parententries": [],
        "subentries": [],
        "title": "",
        "xml": "",
        "sortkey": "",
        "doctype": "",
    }

def purge(dictDB: Connection, email: str, historiography: Historiography):
    dictDB.execute("insert into history(entry_id, action, [when], email, xml, historiography) select id, 'purge', ?, ?, xml, ? from entries", (str(datetime.datetime.utcnow()), email, json.dumps(historiography)))
    dictDB.execute("delete from document_parts")
    dictDB.execute("delete from entries")
    dictDB.commit()
    dictDB.execute("vacuum")
    dictDB.commit()
    return True

def showImportErrors(filename: str, truncate: int):
    with open(filename+".err", "r") as content_file:
        content = content_file.read(truncate if truncate > 0 else -1)
    if truncate > 0:
        return {"errorData": content.replace("<", "&lt;"), "truncated": truncate}
    else:
        return content

class ExternalProcessStatus(TypedDict):
    progressMessage: str
    finished: bool
    errors: bool

def import_dictionary(dictDB: Connection, data: bytes, email: str,
                      progress: Callable[[int, int], None], *, purge_entries=False,
                      purge_history=False, filename="") -> int:
    """Store the entry graph and its XML layout in the same transaction."""
    def scan(configs):
        xema = configs["xema"]
        root = xema.get("root")
        entry_tag = xema_get_element_name_from_id(xema, root) if root else ""
        aliased_tags = {name for key in configs["subbing"] if (name := xema_get_element_name_from_id(xema, key)) != key}
        aliases = {}

        def remember_alias(path, name, attrs, identifier):
            # A detached copy has no parent path to distinguish e.g. entry_idiom from entry.
            if name not in aliased_tags:
                return
            root_name, root_attrs = path[0]
            definition = schema_id_for_tag(configs, root_name, root_attrs.get(XEMA_DEFINITION_ATTRIBUTE))
            for ancestor, _ in path[1:]:
                definition = xema_get_id_from_element_name(xema, ancestor, definition)
            definition = xema_get_id_from_element_name(xema, name, definition)
            if definition != name and is_subentry(configs["subbing"], attrs, definition):
                try:
                    aliases[int(identifier)] = definition
                except ValueError:
                    pass  # Not a shared record ID; the importer will allocate one.

        document = read_document(data, entry_tag, on_nested_id=remember_alias if aliased_tags else None)
        return document, ImportEntries(archival=document.archive_offset is not None, aliases=aliases)

    initial = readDictConfigs(dictDB)
    document, state = scan(initial)
    with dictDB:
        dictDB.execute("begin immediate")
        configs = readDictConfigs(dictDB)
        if configs["xema"] != initial["xema"] or configs["subbing"] != initial["subbing"]:
            document, state = scan(configs)
        if not document.entries:
            raise ValueError("The XML file contains no matching entries. The existing dictionary was kept.")
        if purge_entries or purge_history:
            if purge_history:
                dictDB.execute("delete from history")
            else:
                dictDB.execute("""
                    insert into history(entry_id, action, [when], email, xml, historiography)
                    select id, 'purge', ?, ?, xml, ? from entries
                """, (datetime.datetime.now(datetime.timezone.utc).isoformat(), email,
                      json.dumps({"filename": filename})))
            for table in ("document_parts", "sub", "searchables", "linkables", "entries"):
                dictDB.execute(f"delete from {table}")

        position = dictDB.execute("select max(position) from document_parts").fetchone()[0]
        appended = position is not None
        if appended and document.doctype:
            raise ValueError("This XML has a DOCTYPE. Use replacement import to preserve its document declaration.")
        if not appended:
            dictDB.executemany("insert into document_parts(position, markup) values(?, ?)", [
                (-3, document.prolog()),
                (-2, "" if document.standalone_entry else document.markup(document.root_close, document.root_end)),
                (-1, document.markup(document.root_end)),
            ])
            position = 0

        # Let the allocator skip all IDs explicitly used later in this document.
        if document.max_entry_id:
            dictDB.execute("insert into sqlite_sequence(name, seq) select 'entries', ? "
                           "where not exists (select 1 from sqlite_sequence where name='entries')",
                           (document.max_entry_id,))
            dictDB.execute("update sqlite_sequence set seq=max(seq, ?) where name='entries'",
                           (document.max_entry_id,))

        start = document.prolog_end
        if appended:
            prolog = document.prolog(max(document.declaration_end, 3 if data.startswith(b"\xef\xbb\xbf") else 0))
            if prolog:
                position += 1
                dictDB.execute("insert into document_parts(position, markup) values(?, ?)", (position, prolog))
        anchored = {row[0] for row in dictDB.execute(
            "select entry_id from document_parts where entry_id is not null")}
        for count, span in enumerate(document.entries, 1):
            xml = document.markup(span.start, span.end)
            entry_id = save_imported_record(dictDB, configs, state, xml, span.inherited, document.doctype, email,
                                            inherited_preserve=span.inherited_preserve)
            placement = entry_id if entry_id not in anchored else None
            anchored.add(entry_id)
            position += 1
            dictDB.execute("insert into document_parts(position, markup, is_slot, entry_id) values(?, ?, 1, ?)",
                           (position, document.markup(start, span.start), placement))
            start = span.end
            if count % 100 == 0:
                progress(count, span.end)
        remainder_end = len(data) if appended else (
            document.root_end if document.standalone_entry else document.root_close)
        if start < remainder_end:
            dictDB.execute("insert into document_parts(position, markup) values(?, ?)",
                           (position + 1, document.markup(start, remainder_end)))

        finish_import_references(dictDB, configs, state)
    return len(document.entries)


def save_imported_record(dictDB: Connection, configs: Configs, state: ImportEntries, xml: str,
                         inherited: dict[str, str], doctype: str, email: str, *, inherited_preserve: bool) -> int:
    """Use the same index projection as reindexing for entries needing no XML transformation."""
    fields = None
    if (not doctype and not inherited and not configs["links"] and "<" + SUBENTRY not in xml and EMBEDDED not in xml
            and "lxnm:linkable" not in xml and "lxnm:entryID" not in xml
            and XEMA_DEFINITION_ATTRIBUTE not in xml and "<!" not in xml and "<?" not in xml):
        fields = quick_entry_text(xml)
    if fields is not None:
        node = fields.root
        stored_id = node.get(f"{{{LXNM}}}id")
        if ((stored_id is None or (stored_id.isascii() and stored_id.isdigit() and len(stored_id) <= 19
                                  and 0 < int(stored_id) < 2**63 - 1
                                  and int(stored_id) not in state.defined and int(stored_id) not in state.aliases))
                and (state.archival or not requires_xml_transform(configs, node))):
            entry_id = int(stored_id) if stored_id is not None else None
            is_new = True
            if entry_id is None:
                entry_id = dictDB.execute("insert into entries(doctype) values(?)", (node.tag,)).lastrowid
                attrs = f' lxnm:id="{entry_id}"'
                if node.nsmap.get("lxnm") != LXNM:
                    attrs += f' xmlns:lxnm="{LXNM}"'
                xml = add_attributes(xml, node.tag, attrs)
            else:
                is_new = dictDB.execute("insert into entries(id) values(?) on conflict(id) do nothing",
                                        (entry_id,)).rowcount > 0
                if not is_new:
                    for table, key in (("searchables", "entry_id"), ("linkables", "entry_id"), ("sub", "parent_id")):
                        dictDB.execute(f"delete from {table} where {key}=?", (entry_id,))
            state.defined[entry_id] = inherited_preserve
            definition = schema_id_for_tag(configs, node.tag)
            title, title_html = get_entry_title(fields, configs, definition)
            dictDB.executemany(INSERT_SEARCHABLE, entry_searchables(configs, fields, entry_id, title))
            dictDB.execute("update entries set doctype=?, xml=?, title=?, sortkey=?, flag=?, needs_update=0 where id=?",
                           (node.tag, xml, title_html, get_entry_sortkey(fields, configs),
                            get_entry_flag(fields, configs), entry_id))
            dictDB.execute("insert into history(entry_id, action, [when], email, xml, historiography) values(?,?,?,?,?,?)",
                           (entry_id, "create" if is_new else "update",
                            datetime.datetime.now(datetime.timezone.utc).isoformat(), email, xml, "{}"))
            return entry_id

    tag = parse(xml, doctype=doctype)
    for name, value in inherited.items():
        tag.attrs.setdefault(name, value)
    entry_id, _, success, _ = createEntry(dictDB, configs, tag, email, commit=False, importing=state,
                                         inherited_preserve=inherited_preserve)
    if not success:
        raise ValueError("Could not import an XML entry.")
    return entry_id


def requires_xml_transform(configs: Configs, root) -> bool:
    """Find candidates that need schema-aware extraction or automatic numbering."""
    xema = configs["xema"]
    for definition, rule in configs["subbing"].items():
        name = xema_get_element_name_from_id(xema, definition)
        attributes = rule.get("attributes") or {}
        if ":" in name or any(":" in attribute for attribute in attributes):
            return True
        if any(not attributes or any(
            attr in node.attrib and (not value or node.attrib[attr] == value) for attr, value in attributes.items()
        ) for node in root.iterdescendants(name)):
            return True
    for rule in configs.get("autonumbering", {}).values():
        if not rule.get("auto_apply"):
            continue
        name = xema_get_element_name_from_id(xema, rule.get("element", ""))
        target = rule.get("target") or ""
        if ":" in name or not target.startswith("@"):
            return True
        attr = target[1:].replace("xml:", "{http://www.w3.org/XML/1998/namespace}", 1)
        if any(not node.get(attr) or (
            rule.get("overwrite_existing") and not (rule.get("type", "number") == "number" and rule.get("number_globally"))
        ) for node in root.iter(name)):
            return True
    return False


def subentry_label(dictDB: Connection, configs: Configs, entry_id: int,
                   labels: dict[int, tuple[str, str] | None]) -> tuple[str, str] | None:
    if entry_id not in labels:
        row = dictDB.execute("select doctype, xml from entries where id=?", (entry_id,)).fetchone()
        if row is None:
            labels[entry_id] = None
        else:
            fields, definition = index_fields(configs, row["xml"], row["doctype"])
            labels[entry_id] = (get_entry_title(fields, configs, definition)[0], row["doctype"])
    return labels[entry_id]


def refresh_subentry_markers(dictDB: Connection, configs: Configs, xml: str,
                             labels: dict[int, tuple[str, str] | None], *, on_reference=None) -> str:
    def resolve(target):
        label = subentry_label(dictDB, configs, target, labels) if target is not None else None
        if on_reference is not None:
            on_reference(target, label)
        if label is None:
            return None
        title, doctype = label
        return f'<{SUBENTRY} doctype={quoteattr(doctype)} id="{target}" title={quoteattr(title)}></{SUBENTRY}>'

    return rewrite(xml, resolve=resolve)


def finish_import_references(dictDB: Connection, configs: Configs, state: ImportEntries):
    labels = {}
    for entry_id in state.deferred:
        xml = dictDB.execute("select xml from entries where id=?", (entry_id,)).fetchone()[0]
        children = set()

        def collect(target, label):
            if label is None:
                raise ValueError(f"Entry {entry_id} references missing subentry {target}.")
            children.add(target)

        refreshed = refresh_subentry_markers(dictDB, configs, xml, labels, on_reference=collect)
        dictDB.executemany("insert into sub(parent_id, child_id) values(?, ?)",
                           ((entry_id, child_id) for child_id in children))
        if refreshed != xml:
            dictDB.execute("update entries set xml=? where id=?", (refreshed, entry_id))
    parents = dictDB.execute("select distinct parent_id, child_id from sub").fetchall()
    affected = {parent for parent, child in parents if child in state.defined and parent not in state.defined}
    dictDB.executemany("update entries set needs_update=1 where id=? and needs_update=0",
                       ((parent,) for parent in affected))


def importfile(dictID: str, filepath: str, user: str, purge: bool = False) -> ExternalProcessStatus:
    # TODO port to bgjob?
    dbpath = os.path.join(siteconfig["dataDir"], "dicts", dictID+".sqlite")
    args = ["--remove-upload"]
    if purge:
        args.append("-pp") # purge both entries AND history
    args.append("-u")
    args.append(user)
    args.append(dbpath)
    args.append(filepath)
    return _startSubprocess(subProcessID = filepath, scriptPath = os.path.join(API_DIR, "adminscripts", "import.py"), args = args)

def getImportStatus(filepath: str) -> ExternalProcessStatus:
    return _getProcessStatus(filepath + ".pid", filepath + ".err")

def _startSubprocess(subProcessID: str, scriptPath: str, args: list[str]) -> ExternalProcessStatus:
    "Start the subprocess if it is not already running or finished. Return the status of the process if is was already running."
    import subprocess
    import sys
    from threading import Thread
    pidfile = subProcessID + ".pid"
    errfile = subProcessID + ".err"
    lockfile = pidfile + ".lock"
    try:
        with open(lockfile, "x"):
            pass
    except FileExistsError:
        return _getProcessStatus(pidfile, errfile)

    try:
        with open(pidfile, "w") as stdout, open(errfile, "w") as stderr:
            process = subprocess.Popen([sys.executable, scriptPath, *args], stdout=stdout, stderr=stderr,
                                       start_new_session=True, close_fds=True)
    except OSError:
        os.unlink(lockfile)
        raise

    def record_failure():
        exit_status = process.wait()
        if exit_status and os.stat(errfile).st_size == 0:
            with open(errfile, "w") as errors:
                errors.write(f"The import process stopped before it finished (exit status {exit_status}).\n")

    Thread(target=record_failure, daemon=True).start()
    return {
        "errors": False,
        "finished": False,
        "progressMessage": "Started. Please wait..."
    }

def _getProcessStatus(pidfile: str, errfile: str) -> ExternalProcessStatus:
    """read the pidfile and errfile and return the status of the proces.
    When the pidfile ends with a line

    Args:
        pidfile (str): file path to the console output file
        errfile (str): file path to the error output file
    """
    if not os.path.exists(pidfile):
        return {
            "finished": True,
            "errors": False,
            "progressMessage": "Finished",
        }

    progress = 'Import started. Please wait...'
    errors = os.path.isfile(errfile) and os.stat(errfile).st_size > 0
    with open(pidfile, "r") as content_file:
        lines = [line.strip() for line in content_file if line.strip()]
        if lines:
            progress = lines[-1]

    finished = bool(re.fullmatch(r"100% - [0-9]+ total entries imported\.", progress))
    return {"progressMessage": progress, "finished": finished, "errors": errors}

def readDoctypesUsed(dictDB: Connection):
    c = dictDB.execute("select doctype from entries group by doctype order by count(*) desc")
    doctypes: list[str] = []
    for r in c.fetchall():
        doctypes.append(r["doctype"])
    return doctypes

def getLastEditedEntry(dictDB: Connection, email: str):
    c = dictDB.execute("select entry_id from history where email=? order by [when] desc limit 1", (email, ))
    r = c.fetchone()
    if r:
        return str(r["entry_id"])
    else:
        return ""

def getDictStats(dictDB: Connection):
    res = {"entryCount": 0, "needUpdate": 0}
    c = dictDB.execute("select count(*) as entryCount from entries")
    r = c.fetchone()
    res["entryCount"] = r["entryCount"]
    c = dictDB.execute("select count(*) as needUpdate from entries where needs_update > 0")
    r = c.fetchone()
    res["needUpdate"] = r["needUpdate"]
    return res

def updateDictConfig(dictDB: Connection, dictID: str, configID: str, content: Any) -> Any:
    with dictDB:
        dictDB.execute("insert into configs(id, json) values(?, ?) on conflict(id) do update set json=excluded.json",
                       (configID, json.dumps(content)))
        if configID in {"subbing", "links", "autonumbering", "xema"}:
            mark_index_pending(dictDB, structural=True)
        elif configID in {"titling", "searchability", "flagging"}:
            mark_index_pending(dictDB)

    # post-process actions
    if configID == "ident":
        attachDict(dictDB, dictID)
        if content.get('lang'):
            lang = content.get('lang')
            with getMainDB() as conn:
                conn.execute("UPDATE dicts SET language=? WHERE id=?", (lang, dictID))
                conn.commit()    
    elif configID == 'users':
        attachDict(dictDB, dictID)

    return content


def mark_index_pending(dictDB: Connection, *, structural: bool = False):
    pending = 2 if structural else 1
    dictDB.execute("update entries set needs_update=? where coalesce(needs_update, 0) < ?", (pending, pending))


def reindex_entries(dictDB: Connection, *, limit: int = 1024, ids: list[int] | None = None) -> int:
    """Refresh derived search data in one transaction, reserving XML rewrites for structure changes."""
    where = "needs_update > 0"
    params = ()
    if ids is not None:
        where += f" and id in ({','.join('?' * len(ids))})"
        params = tuple(ids)
    else:
        where += " order by needs_update desc, id limit ?"
        params = (limit,)
    if not dictDB.execute(f"select 1 from entries where {where}", params).fetchone():
        return 0

    with dictDB:
        dictDB.execute("begin immediate")
        configs = readDictConfigs(dictDB)
        rows = dictDB.execute(f"select id, xml, doctype, needs_update from entries where {where}", params).fetchall()
        updates = []
        searchables = []
        labels = {}
        for row in rows:
            entry_id, xml, doctype, pending = row
            fields, definition = index_fields(configs, xml, doctype)
            has_references = "<" + SUBENTRY in xml
            if pending == 2 and (has_references or not isinstance(fields, EntryText) or configs["links"]
                                 or "lxnm:linkable" in xml or XEMA_DEFINITION_ATTRIBUTE in xml
                                 or requires_xml_transform(configs, fields.root)):
                _, _, success, _ = createEntry(dictDB, configs, xml, "system@lexonomy", id=entry_id,
                                               commit=False, maintenance=True)
                if not success:
                    raise ValueError(f"Could not rebuild entry {entry_id}.")
                continue
            if has_references:
                refreshed = refresh_subentry_markers(dictDB, configs, xml, labels)
                if refreshed != xml:
                    dictDB.execute("update entries set xml=? where id=?", (refreshed, entry_id))
            title, title_html = get_entry_title(fields, configs, definition)
            updates.append((title_html, get_entry_sortkey(fields, configs), get_entry_flag(fields, configs), entry_id))
            searchables.extend(entry_searchables(configs, fields, entry_id, title))
        dictDB.executemany("delete from searchables where entry_id=?", [(update[-1],) for update in updates])
        dictDB.executemany(INSERT_SEARCHABLE, searchables)
        dictDB.executemany("update entries set title=?, sortkey=?, flag=?, needs_update=0 where id=?", updates)
    return len(rows)


def getEntryLinks(dictDB: Connection, dictID: str, entryID: int, reader: User):
    ret = {"out": [], "in": []}
    cl = dictDB.execute("SELECT count(*) as count FROM sqlite_master WHERE type='table' and name='linkables'")
    rl = cl.fetchone()
    if rl['count'] > 0:
        c = dictDB.execute("SELECT * FROM linkables WHERE entry_id=?", (entryID,))
        for r in c.fetchall():
            for lr in links_get(dictID, r["element"], r["txt"], "", "", "", reader):
                lr['source_preview'] = r['preview']
                ret["out"].append(lr)
            for lr in links_get("", "", "", dictID, r["element"], r["txt"], reader):
                lr['target_preview'] = r['preview']
                ret["in"].append(lr)
    return ret

def readDictHistory(dictDB: Connection, dictID: str, configs: Configs, entryID: int) -> List[HistoryEntry]:
    html_transformer = get_xslt_transformer(configs.get("xemplate", {}).get("_xsl", ""))

    history: List[HistoryEntry] = []
    c = dictDB.execute("select * from history where entry_id=? order by [when] desc", (entryID,))
    for row in c.fetchall():
        xml = row["xml"]
        historiography = json.loads(row["historiography"] or "{}")
        if historiography.pop("apikey", None):
            historiography["viaApi"] = True
        revision: HistoryEntry = {
            "entry_id": row["entry_id"],
            "revision_id": row["id"],
            "content": xml or "",
            "action": row["action"],
            "when": row["when"],
            "email": row["email"] or "",
            "historiography": historiography
        }
        if xml:
            parsed = parse(xml)
            revision["schemaId"] = entry_schema_id(configs, parsed)
            revision.update(get_entry_rendering(dictDB, parsed, html_transformer))
        history.append(revision)
    return history

def links_add(source_dict: str, source_el: str, source_id: str, target_dict: str, target_el: str, target_id: str, confidence: float=0, conn: Optional[Connection]=None):
    if not conn:
        conn = getLinkDB()
    c = conn.execute("SELECT * FROM links WHERE source_dict=? AND source_element=? AND source_id=? AND target_dict=? AND target_element=? AND target_id=?", (source_dict, source_el, source_id, target_dict, target_el, target_id))
    row = c.fetchone()
    if not row:
        conn.execute("INSERT INTO links (source_dict, source_element, source_id, target_dict, target_element, target_id, confidence) VALUES (?,?,?,?,?,?,?)", (source_dict, source_el, source_id, target_dict, target_el, target_id, confidence))
        conn.commit()
    c = conn.execute("SELECT * FROM links WHERE source_dict=? AND source_element=? AND source_id=? AND target_dict=? AND target_element=? AND target_id=?", (source_dict, source_el, source_id, target_dict, target_el, target_id))
    row = c.fetchone()
    return {"link_id": row["link_id"], "source_dict": row["source_dict"], "source_el": row["source_element"], "source_id": row["source_id"], "target_dict": row["target_dict"], "target_el": row["target_element"], "target_id": row["target_id"], "confidence": row["confidence"]}

def links_delete(dictID: str, linkID: str):
    conn = getLinkDB()
    conn.execute("DELETE FROM links WHERE source_dict=? AND link_id=?", (dictID, linkID))
    conn.commit()
    c = conn.execute("select * from links where link_id=?", (linkID, ))
    if len(c.fetchall()) > 0:
        return False
    else:
        return True

def links_get(source_dict: str, source_el: str, source_id: str, target_dict: str, target_el: str, target_id: str, reader: User):
    filters = {
        "source_dict": source_dict, "source_element": source_el, "source_id": source_id,
        "target_dict": target_dict, "target_element": target_el, "target_id": target_id,
    }
    where = {field: value for field, value in filters.items() if value}
    clause = " AND ".join(field + "=?" for field in where)
    links, _ = _read_links(reader, clause, tuple(where.values()))
    return links


def read_dictionary_links(dict_id: str, reader: User):
    links, dictionaries = _read_links(reader, "source_dict=? OR target_dict=?", (dict_id, dict_id),
                                      include_dictionaries=True)
    return {
        "links": {
            "to": [link for link in links if link["source_dict"] == dict_id],
            "from": [link for link in links if link["target_dict"] == dict_id],
        },
        "dictionaries": dictionaries,
    }


def _read_links(reader: User, where: str, params: tuple[str, ...], *, include_dictionaries: bool = False):
    query = "SELECT * FROM links" + (" WHERE " + where if where else "")
    with ExitStack() as connections:
        links_db = connections.enter_context(closing(getLinkDB()))
        readable = {}

        def open_readable(dict_id):
            if dict_id not in readable:
                readable[dict_id] = None
                try:
                    db = connections.enter_context(closing(getDB(dict_id)))
                except OSError:
                    return None
                configs = readDictConfigs(db)
                if configs["publico"]["public"] or (
                    reader["loggedin"] and (reader.get("isAdmin") or reader["email"] in configs["users"])
                ):
                    readable[dict_id] = (db, configs)
            return readable[dict_id]

        def entry_info(dictionary, element, link_id):
            if dictionary is None:
                return "", "", "", ""
            db, configs = dictionary
            entry_id = ""
            preview = ""
            try:
                row = db.execute("SELECT entry_id, preview FROM linkables WHERE element=? AND txt=?",
                                 (element, link_id)).fetchone()
                if row:
                    entry_id = str(row["entry_id"])
                    preview = " ".join((row["preview"] or "").split()[:7])
            except sqlite3.OperationalError:
                pass  # Old dictionaries may not have the linkables table.
            if not entry_id and re.fullmatch(r"[0-9]+_[0-9]+", link_id):
                entry_id = link_id.split("_")[0]
            records = readEntries(db, configs, int(entry_id), titlePlain=True) if entry_id else []
            if records:
                return entry_id, records[0].get("titlePlain", ""), preview, records[0]["doctype"]
            return entry_id, "", preview, ""

        results = []
        dictionaries = {}
        for row in links_db.execute(query, params):
            source_dict_id, target_dict_id = row["source_dict"], row["target_dict"]
            source = open_readable(source_dict_id)
            target = open_readable(target_dict_id)
            external = target is None and target_dict_id in {"BABELNET", "CILI"} and not dictExists(target_dict_id)
            if source is None or (target is None and not external):
                continue
            if include_dictionaries:
                for dict_id, dictionary in ((source_dict_id, source), (target_dict_id, target)):
                    if dict_id in dictionaries:
                        continue
                    ident = dictionary[1]["ident"] if dictionary else {}
                    dictionaries[dict_id] = {
                        "title": ident.get("title", dict_id),
                        "blurb": markdown_text(str(ident.get("blurb") or "")),
                        "isExternal": dictionary is None,
                    }
            source_entry, source_hw, source_preview, source_doctype = entry_info(source, row["source_element"], row["source_id"])
            target_entry, target_hw, target_preview, target_doctype = entry_info(target, row["target_element"], row["target_id"])
            if external and row["target_dict"] == "CILI":
                target_entry = target_hw = row["target_id"]
            results.append({
                "link_id": row["link_id"],
                "source_dict": row["source_dict"],
                "source_entry": source_entry,
                "source_doctype": source_doctype,
                "source_hw": source_hw,
                "source_el": row["source_element"],
                "source_id": row["source_id"],
                "source_preview": source_preview,
                "target_dict": row["target_dict"],
                "target_entry": target_entry,
                "target_doctype": target_doctype,
                "target_hw": target_hw,
                "target_el": row["target_element"],
                "target_id": row["target_id"],
                "target_preview": target_preview,
                "confidence": row["confidence"],
            })
        return results, dictionaries


def getDictLinkables(dictDB: Connection):
    ret = []
    cl = dictDB.execute("SELECT count(*) as count FROM sqlite_master WHERE type='table' and name='linkables'")
    rl = cl.fetchone()
    if rl['count'] > 0:
        c = dictDB.execute("SELECT * FROM linkables ORDER BY entry_id, element, txt")
        for r in c.fetchall():
            ret.append({"element": r["element"], "link": r["txt"], "entry": r["entry_id"], "preview": r["preview"]})
    return ret

def addAutoNumbers(dictDB: Connection, configs: Configs, user: User):
    """Runs the autonumbering operation in manual mode"""
    config = configs.get("autonumbering")
    if not config or not (len(config)):
        return {"success": True, "processed": 0}
    total = 0
    for e in dictDB.execute("select id, xml from entries").fetchall():
        id = e["id"]
        xml = parse(e["xml"])
        entry_was_updated = presave_autonumbering(dictDB, configs, xml, isAutoApplying = False)
        if not entry_was_updated:
            continue

        total += 1
        xmlstr = str(xml)
        dictDB.execute("insert into history(entry_id, action, [when], email, xml, historiography) values(?, ?, ?, ?, ?, ?)", (id, "autonumber", str(datetime.datetime.utcnow()), user["email"], xmlstr, json.dumps({})))
        dictDB.execute("update entries set xml = ? where id = ?", (xmlstr, id))

    dictDB.commit()
    return {"success": True, "processed": total}

def notifyUsers(configOld: ConfigUsers, configNew: ConfigUsers, dictInfo: ConfigIdent, dictID: str):
    for user in configNew:
        if not configOld.get(user):
            mailSubject = "Lexonomy, added to the dictionary"
            mailText = "Dear Lexonomy user,\n\n"
            mailText += "you are now able to access the following dictionary:\n"
            mailText += "  " + dictInfo['title'] + "\n\n"
            mailText += "You have the following permissions:\n"
            if configNew[user]['canEdit']:
                mailText += " * edit\n"
            if configNew[user]['canConfig']:
                mailText += " * configure\n"
            if configNew[user]['canDownload']:
                mailText += " * download\n"
            if configNew[user]['canUpload']:
                mailText += " * upload\n"
            mailText += "\nYou can access the dictionary at the following address:\n"
            mailText += siteconfig["clientUrl"] + "#/" + dictID
            mailText += "\n\nYours,\nThe Lexonomy team"
            try:
                sendmail(user, mailSubject, mailText)
            except Exception as e:
                pass

def changeFavDict(userEmail: str, dictID: str, status: Literal["true"]):
    if userEmail != '' and dictID != '':
        with getMainDB() as conn:
            conn.execute("DELETE FROM dict_fav WHERE user_email=? AND dict_id=?", (userEmail, dictID))
            if status == 'true':
                conn.execute("INSERT INTO dict_fav VALUES (?, ?)", (dictID, userEmail))
            conn.commit()
    return True

def get_iso639_1() -> List[IsoCode]:
    codes = []
    with (API_DIR / "resources" / "iso-639-3.tab").open(encoding="utf-8") as languages:
        for line in languages:
            la = line.split("\t")
            if la[3] != "" and la[3] != "Part1":
                codes.append({'code':la[3], 'code3':la[1], 'lang':la[6]})
    return codes

def get_locales():
    codes = []
    for code in Locale().getAvailableLocales():
        codes.append({'code': code, 'lang': Locale(code).getDisplayName()})
    return codes

