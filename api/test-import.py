from __future__ import annotations

import inspect
from contextlib import closing
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
import traceback
from typing import TYPE_CHECKING, Any, Callable, Optional, TypedDict, Union
from unittest.mock import patch

from bs4 import Tag
from siteconfig import read_siteconfig

if TYPE_CHECKING:
    from ops import Configs

# Run python3 test-import.py from api to check imports against a temporary database.

# Some documentation:
# testables array contains objects that each describe a "test"
# a "test" is basically just a list of commands to execute, the rest of the object is parameters for those commands
# It's written a little ad-hoc but works well enough.

class LinkablesTests(TypedDict):
    txt: list[str]
    "The expected ids of the elements (as defined by ConfigLinks['identifier'] that were made linkable, in no particular order"
    preview: list[str]
    "The expected previews of the elements (as defined by ConfigLinks['preview']) that were made linkable, in no particular order"
    element: list[str]
    "The expected xml element names of the elements that were made linkable, in no particular order"

class Test(TypedDict):
    description: str
    "Describe the test, this is printed to the console on evaluation along with pass/fail status"
    entry: str
    """The entry xml to index. This is assumed to be valid xml, 
    though namespace declarations are optional 
    because we're assuming document fragments, where the header declaring the namespace has been cut off"""
    
    # Here are some properties that are tested after the import is complete
    id: Union[int, Callable[[int], bool]]
    """Either the ID that the imported entry is expected to have, 
    or a lambda that receives the ID the entry got and returns a bool (for comparisons like ID is in a certain range, or not null, or what whatever)"""
    xml: Union[str, Callable[[str], bool]]
    """Same as ID, but for the indexed xml. Meaning after lexonomy ID attributes added, subentry substition, linking attributes added, etc.
        Note that all whitespace (both in database and in this property) is stripped before comparing because it's not relevant.
        This is a pretty lazy string-compare though, so order of attributes, quotes, etc should be an exact match though.
    """
    doctype: Union[str, Callable[[str], bool]]
    """Same as ID, but for the entry's doctype (doctype is the element name of its root node)"""
    title: Union[str, Callable[[str], bool]]
    """Same as ID, but for the title of the entry. NOTE: the title is an html-string"""
    sortkey: Union[str, Callable[[str], bool]]
    """Same as ID, but for the sortkey, this will usually be the headword"""
    searchables: Union[list[str], Callable[[list[str]], bool]]
    """Same as ID, but for the searchables, this will usually only be the headword and title, but more can be specified by the user"""
    subentries: list[str]
    """List of IDS for the entry's subentries. These are validated against the database."""
    subentrytests: dict[int, Any] # really another Test instance
    """Keyed by subentry ID: tests/comparisons for the subentry's properties (such as sortkey, title, doctype, etc). This may contain more subentrytests for the subentry's subentries, because they can be recursive."""
    
    linkables: LinkablesTests
    """Values that the linkables table should have for the entry"""

    configs: Configs
    """A partial config object (with xema, flagging, titling, etc.) used to specificy specific config settings for this test."""
    
    actions: list[Any]
    """The actions to perform before testing the results
        Possible actions right now: "create" (index the entry), "flag" (flag an entry), "delete" (delete an entry)
        If just a string is used (such as actions: ["create"]) the action is used without arguments.
        To pass arguments to the function (createEntry, set_entry_flag, deleteEntry) use a nested array with the arguments:
        actions: ["create", ["delete", 100]] # first run create action, then delete action for entry ID 100.
    """

test_directory = TemporaryDirectory(prefix="lexonomy-import-")
test_config_path = Path(test_directory.name) / "siteconfig.json"
test_config = read_siteconfig(Path("../config/siteconfig.example.json"))
test_config.update(dataDir=test_directory.name, admins=[])
test_config_path.write_text(json.dumps(test_config), encoding="utf-8")
os.environ["LEXONOMY_SITECONFIG"] = str(test_config_path)
subprocess.run([sys.executable, "adminscripts/init.py"], check=True)

with patch("siteconfig.SITECONFIG_PATH", test_config_path):
    import ops

ops.makeDict("#test", "blank", "test", "test", "root@localhost")

dictDB = ops.getDB("#test")
configsFromDB = ops.readDictConfigs(dictDB)

def dict_factory(cursor, row):
    """Transform sqlite query results into normal {} dictionaries so we can use them with JSON functions etc, because normally there are a load of unserializable properties in those row objects that we don't need."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
dictDB.row_factory = dict_factory

testables = [{
    "description": """Test entry without any further content. Id and lexonomy namespace should be added, sortkey, title and searchables should default to "?".""",

    "entry": """<entry></entry>""",

    "id": lambda x: x != None,
    "doctype": "entry",
    "title": "<span class='headword'>?</span>",
    "sortkey": "?",
    "searchables": ["?"]
}, {
    "description": "Test that sortkey, searchable and title use the first available text if there is no headword element",

    "entry": """<entry><first_text>yes</first_text>no<some_element>no</some_element></entry>""",

    "doctype": "entry",
    "title": "<span class='headword'>yes</span>",
    "sortkey": "yes",
    "searchables": ["yes"],
}, {
    "description": "Test that id is preserved when already present",

    "entry": """<entry lxnm:id="10"></entry>""",

    "id": 10,
}, {
    "description": "Test that id outside namespace is ignored",

    "entry": """<entry id="10"></entry>""",

    "id": lambda x: x != 10, # passing an id, but not an lxnm:id, so the auto-assigned id should not be 10, because the id attribute should be ignored.
}, {
    "description": "Title is extracted properly",

    "configs": {
        "titling": {
            "headword": "title"
        }
    },

    "entry": """
    <entry id="10">
        <text>this is some text</text>
        <content>
            <title>this is the title</title>
        </content>
        <text>this is some other text</text>
    </entry>""",

    "title": "<span class='headword'>this is the title</span>",
    "sortkey": "this is the title", # sortkey is headword
    "searchables": ["this is the title"] # searchables are headword + title (which is first text if not headword)
}, {
    "description": "HeadwordAnnotations works, extra searchable elements work (also when xema is using elementName).",

    "configs": {
        "titling": {
            "headword": "title",
            "headwordAnnotations": ["text"]
        },
        "searchability": {
            "searchableElements": ["text", "searchable_element_id"]
        },
        "xema": {
            "elements": {
                "searchable_element_id": {"elementName": "searchable_element"}
            }
        }
    },

    "entry": """
    <entry id="10">
        <text>this is some text</text>
        <content>
            <title>this is the title</title>
        </content>
        <text>this is some other text</text>
        <searchable_element>content of the searchable_element</searchable_element>
    </entry>""",

    "title": "<span class='headword'>this is the title</span> this is some text",
    "sortkey": "this is the title",
    # headword, title (headword + content of the first text node, because of headwordAnnotations), contents of the two text elements.
    "searchables": ["this is the title", "this is the title this is some text", "this is some text", "this is some other text", "content of the searchable_element"]
}, {
    "description": "titling headwordAnnotations works also when elementName is used in the xema.",

    "configs": {
        "titling": {
            "headword": "title",
            "headwordAnnotations": ["text_id"]
        },
        "xema": {
            "elements": {
                "text_id": {"elementName": "text"}
            }
        }
    },

    "entry": """
    <entry id="10">
        <text>this is some text</text>
        <content>
            <title>this is the title</title>
        </content>
        <text>this is some other text</text>
    </entry>""",

    "title": "<span class='headword'>this is the title</span> this is some text",
}, {
    "description": "HeadwordAnnotationsAdvanced works",

    "configs": {
        "titling": {
            "headwordAnnotationsType": "advanced",
            "headwordAnnotationsAdvanced": "<div class='test'>%(title)</div><div>%(no_match)</div>"
        },
    },

    "entry": """
    <entry id="10">
        <text>this is some text</text>
        <content>
            <title>this is the title</title>
        </content>
        <title>this is another title that should be ignored because it is later in the document</title>
        <text>this is some other text</text>
    </entry>""",

    "title": "<div class='test'>this is the title</div><div>%(no_match)</div>",
    "sortkey": "this is some text", # first text in the entry since nothing defined
    # headword (first text in entry because not otherwise defined) + text content of matched escape sequences in headwordAnnotationsAdvanced
    "searchables": ["this is some text", "this is the title"]
}, {
    "description": "Subentry works with some interesting edge cases.",

    "configs": {
        "titling": {
            "headword": "headword",
            "headwordAnnotations": ["text"], # make extracting the entry title difficult due to titles existing in subentries and main entry alike
        },
        "subbing": {
            "sub": {}
        },
        "searchability": {
            "searchableElements": ["text"]
        }
    },

    "entry": """
    <entry lxnm:id="100">
        <text>some other text in the entry</text>
        <sub lxnm:id="101">
            <headword>subentry headword</headword>
            <text>subentry text</text>
        </sub>
        <headword>headword</headword>
        <sub lxnm:id="102"><headword>subentry headword 2</headword></sub>
    </entry>""",

    "sortkey": "headword", # NOTE: ensure the extracted headword is the one actually inside the entry itself - not the headword of one of its subentries
    "searchables": ["headword", "headword some other text in the entry", "some other text in the entry"],
    "xml": """
    <entry lxnm:id="100" xmlns:lxnm="http://www.lexonomy.eu/">
        <text>some other text in the entry</text>
        <lxnm:subentryParent doctype="sub" id="101" title="subentry headword subentry text"></lxnm:subentryParent>
        <headword>headword</headword>
        <lxnm:subentryParent doctype="sub" id="102" title="subentry headword 2"></lxnm:subentryParent>
    </entry>
    """,
    "subentries": [101, 102] # created during import.
},  {
    "description": "Applying a flag works when not configured",
    
    "configs": {
        "flagging": {
            "flag_element": "flag",
            "flags": [{
                "key": "", # keyboard shortcut
                "name": "test", # flag element content
                "label": "", # clientside tooltip
                "color": ""
            }]
        }
    },

    "actions": ["create", ["flag", "test"]],

    "entry": """
    <entry lxnm:id="999">
        <text>some content</text>
    </entry>""",

    "xml": """
    <entry lxnm:id="999" xmlns:lxnm="http://www.lexonomy.eu/">
        <text>some content</text>
        <flag>test</flag></entry>
    """,
    "subentries": [],
    "flag": "test"
}, {
    "description": "Applying a flag works when a xema is known and the flag in a far descendant of root",

    "configs": {
        "xema": {
            "root": "entry",
            "elements": {
                "entry": { "children": [{"name": "a"}, {"name": "b"}] },
                "a": { "children": [{"name": "c"}, {"name": "d"}] },
                "c": { "children": [{"name": "e"}, {"name": "f"}] },
                "f": { "children": [{"name": "flag"}] },
            }
        },
        "flagging": {
            "flag_element": "flag",
            "flags": [{
                "key": "", # keyboard shortcut
                "name": "test", # flag element content
                "label": "", # clientside tooltip
                "color": ""
            }]
        }
    },

    "actions": ["create", ["flag", "test"]],

    "entry": """
    <entry lxnm:id="999">
        <text>some content</text>
    </entry>""",

    "xml": """
    <entry lxnm:id="999" xmlns:lxnm="http://www.lexonomy.eu/">
        <text>some content</text>
        <a><c><f><flag>test</flag></f></c></a></entry>
    """,
    "flag": "test"
}, {
    "description": "Applying a flag puts it directly under the root when a xema is known, but the flag is not inside the xema",
    "configs": {
        "xema": {
            "root": "entry",
            "elements": {
                "entry": { "children": [{"name": "a"}, {"name": "b"}] },
                "a": { "children": [{"name": "c"}, {"name": "d"}] },
                "c": { "children": [{"name": "e"}, {"name": "f"}] },
            }
        },
        "flagging": {
            "flag_element": "flag",
            "flags": [{
                "key": "", # keyboard shortcut
                "name": "test", # flag element content
                "label": "", # clientside tooltip
                "color": ""
            }]
        }
    },

    "actions": ["create", ["flag", "test"]],

    "entry": """
    <entry lxnm:id="999">
        <text>some content</text>
    </entry>""",

    "xml": """
    <entry lxnm:id="999" xmlns:lxnm="http://www.lexonomy.eu/">
        <text>some content</text>
        <flag>test</flag></entry>
    """,
}, {
    "description": "Applying a flag creates the correct elements when the xema uses elementName properties",
    "configs": {
        "xema": {
            "root": "entry",
            "elements": {
                "entry": { "children": [{"name": "a"}, {"name": "b"}] },
                "a": { "children": [{"name": "c"}, {"name": "d"}], "elementName": "a_name" },
                "c": { "children": [{"name": "e"}, {"name": "f"}], "elementName": "c_name" },
                "f": { "children": [{"name": "flag"}], "elementName": "f_name" },
                "flag": { "elementName": "flag_name" }
            }
        },
        "flagging": {
            "flag_element": "flag",
            "flags": [{
                "key": "", # keyboard shortcut
                "name": "test", # flag element content
                "label": "", # clientside tooltip
                "color": ""
            }]
        }
    },

    "actions": ["create", ["flag", "test"]],

    "entry": """
    <entry lxnm:id="999">
        <text>some content</text>
    </entry>""",

    "xml": """
    <entry lxnm:id="999" xmlns:lxnm="http://www.lexonomy.eu/">
        <text>some content</text>
        <a_name><c_name><f_name><flag_name>test</flag_name></f_name></c_name></a_name>
    </entry>
    """,
    "flag": "test"
}, {
    "description": "Subentry in subentry works.",
    
    "configs": {
        "subbing": {
            "subentry": {}
        },
    },

    "entry": """
    <entry>
        <text>title</text>
        <subentry lxnm:id="300">
            <subentry lxnm:id="301">
                <text>subentry level 2</text>
            </subentry>
            <text>subentry level 1</text>
        </subentry>
    </entry>""",

    "searchables": ["title"],
    "subentries": [300],
    "subentrytests": {
        300: {
            "searchables": ["subentry level 1"],
            "subentries": [301],
            "subentrytests": {
                301: {
                    "searchables": ["subentry level 2"]
                }
            }
        }
    }
}, {
    "description": "Subentry reference to unknown entry is removed. (there are constraints in the database that make this necessary)",
    
    "entry": """
    <entry lxnm:id="5">
        <text>title</text>
        <lxnm:subentryParent id="20"/>
    </entry>""",

    "xml": """<entry lxnm:id="5" xmlns:lxnm="http://www.lexonomy.eu/"><text>title</text></entry>""",
    "subentries": []
}, {
    "description": "Subentry works with attribute constraints",
    
    "configs": {
        "subbing": {
            "subentry": {
                "attributes": {
                    "att": "true" # @att must be "true"
                }
            }
        },
    },

    "entry": """
    <entry lxnm:id="5">
        <text>title</text>
        <subentry att="false"><text>ignored subentry</text></subentry>
        <subentry lxnm:id="100" att="true"><text>processed subentry</text></subentry>
    </entry>""",

    "xml": """
    <entry lxnm:id="5" xmlns:lxnm="http://www.lexonomy.eu/">
        <text>title</text>
        <subentry att="false">
            <text>ignored subentry</text>
        </subentry>
        <lxnm:subentryParent doctype="subentry" id="100" title="processed subentry"></lxnm:subentryParent>
    </entry>""",
    "subentries": [100]
}, {
    "description": "Creating entry with a subentry, then deleting that subentry: the link with the subentry is removed.",

    "actions": ["create", ["delete", 100]],

    "configs": { "subbing": {"subentry": {} } },

    "entry": """
    <entry lxnm:id="99">
        <text>title</text>
        <subentry lxnm:id="100">
            <text>subentry title</text>
        </subentry>
    </entry>
    """,

    "xml": """
        <entry lxnm:id="99" xmlns:lxnm="http://www.lexonomy.eu/">
            <text>title</text>
        </entry>
    """
}, {
    "description": "Test that legacy lxnm:entryID attribute is converted into new-style lxnm:id attribute",

    "entry": """
    <entry lxnm:entryID="201">some test</entry>
    """,

    "xml": """<entry lxnm:id="201" xmlns:lxnm="http://www.lexonomy.eu/">some test</entry>""",
    "id": 201
}, {
    "description": "Test linkables format-strings work correctly",
    
    "configs": {
        "links": {
            "sense": {
                "linkElement": "sense",
                "identifier": "[%(@sense_id)] %(content) (%(pos))",
                "preview": "%(content) (%(pos))"
            }
        }
    },

    "entry": """
        <entry lxnm:id="201">
            <headword>test</headword>
            <sense sense_id="sense_1">
                <content>the first sense</content>
                <pos>noun</pos>
            </sense>
            <sense sense_id="sense_2">
                <content>the second sense</content>
                <pos>verb</pos>
            </sense>
            <sense>
                <content>the third sense</content>
                <pos>adjective</pos>
            </sense>
        </entry>
    """,

    "linkables": {
        "txt": ["[sense_1] the first sense (noun)", "[sense_2] the second sense (verb)", "[%(@sense_id)] the third sense (adjective)"], # identifiers
        "element": ["sense", "sense", "sense"],
        "preview": ["the first sense (noun)", "the second sense (verb)", "the third sense (adjective)"]
    }
}, {
    "description": "Test autonumbering can place number in element",
    "configs": {"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n", 
        "type": "number"
    }}},
    "entry": """<entry lxnm:id="0"><n/></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n>0</n></entry>"""
}, {
    "description": "Test autonumbering can place string template in element",
    "configs":{"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "type": "string", 
        "string_template": "autonumber %(headword) %(@some-attribute)"
    }}},
    "entry": """<entry lxnm:id="0"><n some-attribute="0"/><headword>test</headword></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n some-attribute="0">autonumber test 0</n><headword>test</headword></entry>"""
}, {
    "description": "Test autonumbering can place string template in attribute",
    "configs": {"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "target": "@id",
        "type": "string", 
        "string_template": "autonumber %(headword) %(@some-attribute)"
    }}},
    "entry": """<entry lxnm:id="0"><n some-attribute="0"/><headword>test</headword></entry>""",
    "xml":   """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n id="autonumber test 0" some-attribute="0"></n><headword>test</headword></entry>"""
}, {
    "description": "Test autonumbering can place string template in child element",
    "configs": {"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "target": "target_element",
        "type": "string", 
        "string_template": "autonumber %(headword) %(@some-attribute)",
        "overwrite_existing": True
    }}},
    "entry": """<entry lxnm:id="0"><n some-attribute="0"><target_element>this value should be overwritten</target_element></n><headword>test</headword></entry>""",
    "xml":   """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n some-attribute="0"><target_element>autonumber test 0</target_element></n><headword>test</headword></entry>"""
}, {
    "description": "Test autonumbering can create child element with string template",
    "configs": {"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "target": "target_element",
        "type": "string", 
        "string_template": "autonumber %(headword) %(@some-attribute)"
    }}},
    "entry": """<entry lxnm:id="0"><n some-attribute="0"></n><headword>test</headword></entry>""",
    "xml":   """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n some-attribute="0"><target_element>autonumber test 0</target_element></n><headword>test</headword></entry>"""
}, {
    "description": "Test autonumbering continues from last known number when numbering globally is enabled",
    "configs":{"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "type": "number", 
        "number_globally": True,
        "number_next": 10
    }}},
    "entry": """<entry lxnm:id="0"><n/><n/></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n>10</n><n>11</n></entry>"""
}, {
    "description": "Test autonumbering does not apply when auto_apply is False",
    "configs": {"autonumbering": {"n": {
        "auto_apply": False,
        "element": "n",
        "type": "number", 
        "number_globally": True,
        "number_next": 10
    }}},
    "entry": """<entry lxnm:id="0"><n/><n/></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n></n><n></n></entry>"""
}, {
    "description": "Test autonumbering manually works even when auto_apply is False",
    "configs": {"autonumbering": {"n": {
        "auto_apply": False,
        "element": "n",
        "type": "number", 
        "number_globally": True,
        "number_next": 10
    }}},
    "entry": """<entry lxnm:id="0"><n/><n/></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n>10</n><n>11</n></entry>""",
    "actions": ["create", "autonumber"]
}, {
    "description": "Test autonumbering ignores next number when not numbering globally",
    "configs": {"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "type": "number", 
        "number_globally": False,
        "number_next": 10
    }}},
    "entry": """<entry lxnm:id="0"><n/><n/></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n>0</n><n>1</n></entry>""",
}, {
    # We don't do this because it causes numbers to go up indefinitely every time an entry is saved
    # Because identifiers changing every time you touch the entry is actually completely useless...
    "description": "Test autonumbering does NOT overwrite existing numeric values automatically when global numbers are enabled",
    "configs": {"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "type": "number", 
        "number_globally": True,
        "number_next": 10,
        "overwrite_existing": True
    }}},
    "entry": """<entry lxnm:id="0"><n/><n>1</n></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n>10</n><n>1</n></entry>""",
}, {
    "description": "Test autonumbering DOES overwrite existing numeric values automatically when global numbers are enabled when not in auto-apply mode",
    "configs": {"autonumbering": {"n": {
        "auto_apply": True,
        "element": "n",
        "type": "number", 
        "number_globally": True,
        "number_next": 10,
        "overwrite_existing": True
    }}},
    "entry": """<entry lxnm:id="0"><n/><n>1</n></entry>""",
    "xml": """<entry lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n>11</n><n>12</n></entry>""",
    "actions": ["create", "autonumber"]
}, {
    "description": "Test autonumbering can write to entry root",
    "configs": {"autonumbering": {"entry": {
        "auto_apply": True,
        "element": "entry",
        "target": "@auto_id",
        "type": "number", 
        "number_globally": True,
        "number_next": 10,
        "overwrite_existing": True
    }}},
    "entry": """<entry lxnm:id="0"><n/><n></n></entry>""",
    "xml": """<entry auto_id="10" lxnm:id="0" xmlns:lxnm="http://www.lexonomy.eu/"><n></n><n></n></entry>""",
}, {
    "description": "Test that parent entry is flagged for update when subentry changes",

    "configs": {
        "titling": {
            "headword": "headword"
        },
        "subbing": {
            "sub": {}
        },
    },

    "entry": """
    <entry lxnm:id="100">
        <headword>headword</headword>
        <sub lxnm:id="101">
            <headword>subentry headword</headword>
        </sub>
    </entry>""",

    "actions": ["create", ["update", "<sub><headword>subentry headword edited</headword></sub>", "test@lexonomy", 101]],

    "needs_update": 1,
}]

def overwriteConfig(originalConfig, overrides):
    """
        Put the values from overrides into originalConfig.
        Recurse if both elements are a map.
    """
    configs = json.loads(json.dumps(originalConfig))
    def replace(putInto, value, key):
            if (existingValue := putInto.get(key)) != None and (type(existingValue) != type(value)):
                raise TypeError("Trying to set property to unsupported type: ", key, description)
            if not isinstance(value, dict) or not key in putInto:
                putInto[key] = value
            else: # property already exists, and is a dictionary, recursive overwrite.
                for subKey in value:
                    replace(putInto[key], value[subKey], subKey)
    for key in overrides:
        replace(configs, overrides[key], key)
    return configs

def failIf(
    description: str,
    property: str,
    got: Any,
    expected: Optional[Any],
    compare: lambda got, expected: bool = lambda x,y: x == y,
    message: Optional[str] = None
):
    """Generic variable comparison function with some console logging

    Args:
        description (str): What test are we running
        property (str): What property in the test are we comparing
        got (Any): What was the result of the test run (usually the value of the property in the database after importing)
        expected (Optional[Any]): What did we expect the result to be? 
        compare: How to compare actual and expected variables
        message (Optional[str], optional): Some additional info to print if not a match

    Raises:
        Exception: when the variables don't match.
    """    

    passed = False
    if callable(expected):
        compare = expected
        expected  = None
    elif not callable(compare):
        compare = lambda x, y: x == y

    passExpected = len(inspect.getfullargspec(compare)[0]) > 1
    passed = compare(got, expected) if passExpected else compare(got)
    if not passed:
        raise Exception(f"""'{description}' - mismatch on '{property}'.
{f'''Expected:
{expected}''' if expected != None else ''}
{f'''Got:
{got}'''}
{f'''Addition info:
{message}''' if message != None else ''}
""")

def arraycompare(a, b) -> bool:
    """Set equality comparator for arrays. Uses 'in' operator to compare"""
    if len(a) != len(b):
        return False
    for v in a:
        if not v in b:
            return False
    return True

def test(tests, id: int, description: str):
    """After doing all the operations, run the database value checks."""

    entry = dictDB.execute("select * from entries where id=?", (id, )).fetchone()
    linkables = dictDB.execute("select json_group_array(txt) as txt, json_group_array(element) as element, json_group_array(preview) as preview from linkables where entry_id = ? group by entry_id", (id, )).fetchone()
    if linkables:
        for key in linkables:
            linkables[key] = json.loads(linkables[key])

    # normalize xml whitespace so we can compare (sort of)
    if "xml" in tests:
        tests["xml"] = re.sub(r"\s", "", tests["xml"])
        entry["xml"] = re.sub(r"\s", "", entry["xml"])

    for key in ["id", "xml", "doctype", "title", "sortkey", "flag", "needs_update"]:
        if key in tests:
            failIf(description, key, entry[key], tests[key], tests[key])

    # Test searchables
    if expectedSearchables := tests.get("searchables"):
        searchables = list(map(lambda r: r["txt"], dictDB.execute("select * from searchables where entry_id=?", (id, )).fetchall()))
        failIf(description, "searchables", searchables, expectedSearchables, arraycompare)

    for key in ["txt", "element", "preview"]:
        if key in tests.get("linkables", {}):
            failIf(description, key, linkables[key], tests["linkables"][key], arraycompare)

    # Test subentries last, because it might be recursive
    if expectedSubentries := tests.get("subentries"):
        subentries = list(map(lambda row: row["child_id"], dictDB.execute("select child_id from sub where parent_id = ?", (id, )).fetchall()))
        failIf(description, "subentries", subentries, expectedSubentries, arraycompare)
        for subentryID, subentryTests in tests.get("subentrytests", {}).items():
            test(subentryTests, subentryID, description + f" [subentry {subentryID}]")

failures = 0
for tests in testables:
    try:
        # Override configs for this test, if supplied.
        configs = overwriteConfig(configsFromDB, tests.get("configs", {}))
        description = tests["description"]

        id: int = None
        xmlAsIndexed: Tag = None
        success: bool = None
        feedback: Optional[str] = None

        for action in tests.get("actions", ["create"]):
            params: list = None
            if isinstance(action, list):
                action, *params = action

            if action == "create":
                id, xmlAsIndexed, success, feedback = ops.createEntry(dictDB, configs, tests["entry"], "test@lexonomy")
                failIf(description, "success", success, tests.get("success", True))
            elif action == "flag":
                ops.set_entry_flag(dictDB, id, params[0], configs, "test@lexonomy", xmlAsIndexed)
            elif action == "autonumber":
                ops.addAutoNumbers(dictDB, configs, {"email": "test@lexonomy"})
            elif action == "delete":
                ops.deleteEntry(dictDB, configs, params[0] if len(params) > 0 else id, "test@lexonomy")
            elif action == "update": 
                ops.createEntry(dictDB, configs, params[0], params[1], params[2])
            else:
                raise ValueError(f"Unknown test action: {action}")

        test(tests, id, description)
        print(f"PASS {description}")

    except Exception as e:
        failures += 1
        if type(e) == Exception:
            print(e, file=sys.stderr)
        else:
            traceback.print_exc()

try:
    xml = '<entry xmlns:lxnm="http://www.lexonomy.eu/"><lxnm:subentryParent id="101"/></entry>'
    markup = ops.get_entry_rendering(dictDB, xml, ops.get_xslt_transformer(None))
    assert "subentry headword edited" in markup["resolvedXml"]
    assert "contentHtml" not in markup
    xslt = """<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
        <xsl:template match="/"><div><xsl:value-of select="entry/sub/headword"/></div></xsl:template>
        </xsl:stylesheet>"""
    markup = ops.get_entry_rendering(dictDB, xml, ops.get_xslt_transformer(xslt))
    assert markup == {"contentHtml": "<div>subentry headword edited</div>"}
    print("PASS Entry rendering resolves subentries for both XML and XSLT responses")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    ops.makeDict("purge-test", "smd", "Import rollback test", "", "root@localhost")
    database = Path(test_directory.name) / "dicts" / "purge-test.sqlite"
    upload = Path(test_directory.name) / "broken.xml"
    upload.write_text("<dictionary><entry><headword>First valid entry</headword></entry><entry>", encoding="utf-8")
    with ops.getDB("purge-test") as conn:
        initial_entries = conn.execute("select xml from entries order by id").fetchall()
        assert initial_entries
        result = subprocess.run([sys.executable, "adminscripts/import.py", "-pp", str(database), str(upload)],
                                capture_output=True, text=True)
        assert result.returncode != 0
        assert conn.execute("select xml from entries order by id").fetchall() == initial_entries
        upload.write_text("<entry><headword>A standalone entry</headword></entry>", encoding="utf-8")
        result = subprocess.run([sys.executable, "adminscripts/import.py", "-pp", str(database), str(upload)],
                                capture_output=True, text=True, check=True)
        assert "100% - 1 total entries imported." in result.stdout
        assert "A standalone entry" in conn.execute("select xml from entries").fetchone()["xml"]
    print("PASS A malformed replacement does not purge existing entries")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    ops.makeDict("preview-regression", "blank", "Preview", "", "root@localhost")
    with closing(ops.getDB("preview-regression")) as preview_db:
        preview_config = ops.readDictConfigs(preview_db)
        assert ops.readRandomOne(preview_db, preview_config)["id"] == 0
        preview_config["xema"]["elements"]["entry"]["elementName"] = "example"
        entry_id, _, success, _ = ops.createEntry(preview_db, preview_config, "<example/>", "test@lexonomy")
        assert success
        assert ops.readRandomOne(preview_db, preview_config)["id"] == entry_id
    print("PASS Entry preview handles empty dictionaries and root definitions with an XML name override")

    users = {"previous@example.org": {"canEdit": True, "canConfig": True, "canUpload": True, "canDownload": True}}
    new_users = {**users, "new@example.org": dict(users["previous@example.org"])}
    with patch.object(ops, "sendmail") as sendmail:
        ops.notifyUsers(users, new_users, {"title": "Preview"}, "preview-regression")
        assert sendmail.call_count == 1
        assert sendmail.call_args.args[0] == "new@example.org"
    print("PASS Dictionary permission notifications handle a newly added user")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    local_xml = Path(test_directory.name) / "fixture-for-xslt.xml"
    local_xml.write_text("<fixture>outside input</fixture>", encoding="utf-8")
    transform = ops.get_xslt_transformer(f"""
        <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
            <xsl:template match="/"><div><xsl:value-of select="document('{local_xml.as_uri()}')/fixture"/></div></xsl:template>
        </xsl:stylesheet>
    """)
    assert transform("<entry/>") is None
    print("PASS Dictionary stylesheets cannot read outside their input")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    for name in ("links-public", "links-private"):
        assert ops.makeDict(name, "smd", name, "**Dictionary description**", "root@localhost")
    with ops.getDB("links-public") as conn:
        ops.updateDictConfig(conn, "links-public", "publico", {"public": True, "licence": "cc-by-4.0"})
    assert ops.links_add("links-public", "entry", "1_1", "links-private", "entry", "1_1")
    anonymous = {"email": "", "loggedin": False}
    member = {"email": "root@localhost", "loggedin": True}
    assert ops.links_get("links-public", "", "", "", "", "", anonymous) == []
    assert ops.read_dictionary_links("links-public", anonymous) == {"links": {"to": [], "from": []}, "dictionaries": {}}
    assert len(ops.links_get("links-public", "", "", "", "", "", member)) == 1
    response = ops.read_dictionary_links("links-public", member)
    assert len(response["links"]["to"]) == 1 and not response["links"]["from"]
    assert response["dictionaries"]["links-private"] == {
        "title": "links-private", "blurb": "<p><strong>Dictionary description</strong></p>", "isExternal": False,
    }
    print("PASS Link results respect the visibility of both dictionaries")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    with closing(ops.getDB("links-public")) as link_db:
        link_config = ops.readDictConfigs(link_db)
        first_id, _, _, _ = ops.createEntry(link_db, link_config, "<entry><headword>Wrong sense</headword></entry>", "test@lexonomy")
        second_id, _, _, _ = ops.createEntry(link_db, link_config, "<entry><headword>Right example</headword></entry>", "test@lexonomy")
        link_db.executemany("insert into linkables(entry_id, txt, element, preview) values (?, ?, ?, ?)", [
            (first_id, "shared", "sense", "Sense preview"),
            (second_id, "shared", "example", "Example preview"),
        ])
        link_db.commit()
    ops.links_add("links-public", "example", "shared", "links-public", "sense", "shared")
    links = ops.links_get("links-public", "example", "shared", "", "", "", {"email": "", "loggedin": False})
    assert len(links) == 1
    assert (links[0]["source_entry"], links[0]["source_preview"]) == (str(second_id), "Example preview")
    assert (links[0]["target_entry"], links[0]["target_preview"]) == (str(first_id), "Sense preview")
    print("PASS Cross-links match element as well as identifier")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    ops.createUser('<user email="mixed@example.org" password="test"/>')
    assert ops.makeDict("mixed-case-login", "blank", "Mixed case", "", "mixed@example.org")
    credentials = ops.login("Mixed@Example.org", "test")
    assert credentials["success"]
    assert ops.verifyLogin("Mixed@Example.org", credentials["key"])["email"] == "mixed@example.org"
    with closing(ops.getDB("mixed-case-login")) as login_db:
        permissions, _ = ops.verifyLoginAndDictAccess("Mixed@Example.org", credentials["key"], login_db)
        assert permissions["canEdit"]
    print("PASS Mixed-case email logs in and retains dictionary permissions")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    assert ops.makeDict("recursive-import", "blank", "Recursive import", "", "root@localhost")
    import_directory = Path(test_directory.name)
    upload = import_directory / "recursive.xml"
    upload.write_text("<dictionary><entry> a <entry>nested</entry> b </entry>separator<entry/></dictionary>", encoding="utf-8")
    ops.importfile("recursive-import", str(upload), "root@localhost")
    deadline = monotonic() + 5
    while not (status := ops.getImportStatus(str(upload)))["finished"] and not status["errors"] and monotonic() < deadline:
        sleep(0.02)
    assert status["finished"] and not status["errors"], status
    with closing(ops.getDB("recursive-import")) as import_db:
        actual = import_db.execute("select xml from entries order by id").fetchall()
        assert len(actual) == 2
        assert ops.parse(actual[0]["xml"]).text == " a nested b "
        assert ops.parse(actual[1]["xml"]).text == ""
        export_xml = "".join(ops.export("-7 recursive import", import_db, ops.readDictConfigs(import_db)))
        assert ops.parse(export_xml).entry.text == " a nested b "
        import_db.execute("update configs set json=? where id='xema'", (json.dumps({"root": "", "elements": {}}),))
        import_db.commit()
        upload.write_text('<entry><entry attribute=">"/></entry>', encoding="utf-8")
        database = import_directory / "dicts" / "recursive-import.sqlite"
        subprocess.run([sys.executable, "adminscripts/import.py", "--purge", str(database), str(upload)],
                       capture_output=True, text=True, check=True)
        actual = import_db.execute("select xml from entries").fetchall()
        assert len(actual) == 1
        assert ops.parse(actual[0]["xml"])["attribute"] == ">"
    print("PASS XML import and export preserve recursive entries and mixed content")

    interrupted = import_directory / "interrupted.py"
    interrupted.write_text('import os\nprint("100% - 100 entries imported so far...", flush=True)\nos._exit(1)\n', encoding="utf-8")
    receipt = str(import_directory / "interrupted")
    ops._startSubprocess(receipt, str(interrupted), [])
    deadline = monotonic() + 5
    while not (status := ops.getImportStatus(receipt))["errors"] and monotonic() < deadline:
        sleep(0.02)
    assert not status["finished"] and status["errors"], status
    assert "stopped before it finished" in ops.showImportErrors(receipt, 100)["errorData"]
    print("PASS A failed import cannot be mistaken for a committed 100% checkpoint")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    source = "<entry>  <term>A &amp; B</term>\n  <![CDATA[<example>]]><!--keep--></entry>"
    assert str(ops.parse(source)) == source
    _, _, success, _ = ops.createEntry(dictDB, configsFromDB, "<entry><term>unfinished", "test@lexonomy")
    assert not success
    print("PASS XML saves reject incomplete entries and keep mixed whitespace, CDATA, and comments")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    definition = {
        "root": "main",
        "elements": {
            "main": {"elementName": "entry", "children": [
                {"name": "cycle", "min": 0, "max": None},
                {"name": "sorting", "min": 0, "max": None},
                {"name": "printed", "min": 0, "max": None},
                {"name": "shared", "min": 0, "max": None},
            ]},
            "cycle": {"children": [{"name": "main", "min": 0, "max": None}]},
            "sorting": {"elementName": "sort"},
            "printed": {"children": [{"name": "local-form", "min": 0, "max": None}]},
            "shared": {"children": [{"name": "shared-form", "min": 0, "max": None}]},
            "local-form": {"elementName": "form.alt"},
            "shared-form": {"elementName": "form.alt"},
        },
    }
    configs = overwriteConfig(configsFromDB, {
        "xema": definition, "titling": {"headwordSorting": "sorting"}, "subbing": {"shared-form": {}},
    })
    source = "<entry><headword>Headword</headword><sort>Sort key</sort><printed><form.alt>Inline</form.alt></printed><shared><form.alt>Shared</form.alt></shared></entry>"
    entry_id, entry, success, _ = ops.createEntry(dictDB, configs, source, "test@lexonomy")
    assert success and entry.printed.find("form.alt").text == "Inline"
    assert entry.shared.find("lxnm:subentryParent") is not None
    _, saved, success, _ = ops.createEntry(dictDB, configs, str(entry), "test@lexonomy", id=entry_id)
    assert success and saved.shared.find("lxnm:subentryParent") is not None
    assert ops.get_entry_sortkey(entry, configs) == "Sort key"
    assert ops.find_path_to_element(definition, "main", "shared-form") == ["shared", "form.alt"]

    configs["subbing"] = {
        "local-form": {"titling": {"headword": "fallback"}},
        "shared-form": {"titling": {"headword": "label"}},
    }
    source = ("<entry><printed><form.alt><fallback>Print title</fallback></form.alt></printed>"
              "<shared><form.alt><fallback>Wrong fallback</fallback><label>Shared title</label></form.alt></shared></entry>")
    parent_id, _, success, _ = ops.createEntry(dictDB, configs, source, "test@lexonomy")
    assert success
    children = dictDB.execute("select child_id from sub where parent_id=?", (parent_id,)).fetchall()
    records = ops.readEntries(dictDB, configs, [row["child_id"] for row in children], titlePlain=True)
    assert {row["schemaId"]: row["titlePlain"] for row in records} == {
        "local-form": "Print title", "shared-form": "Shared title",
    }
    detached = next(row for row in records if row["schemaId"] == "shared-form")
    ops.createEntry(dictDB, configs, detached["xml"], "test@lexonomy", id=detached["id"])
    assert ops.readEntries(dictDB, configs, detached["id"], titlePlain=True)[0]["titlePlain"] == "Shared title"
    source = "<form.alt><fallback>Wrong fallback</fallback><label>Replaced source title</label></form.alt>"
    ops.createEntry(dictDB, configs, source, "test@lexonomy", id=detached["id"])
    reread = ops.readEntries(dictDB, configs, detached["id"], titlePlain=True)[0]
    assert reread["schemaId"] == "shared-form" and reread["titlePlain"] == "Replaced source title"
    print("PASS Xema aliases distinguish identical tags by parent and support recursive flag paths")
except Exception:
    failures += 1
    traceback.print_exc()


try:
    from xml.etree import ElementTree

    assert ops.makeDict("document-roundtrip", "blank", "XML document", "", "root@localhost")
    source = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE dictionary [<!ENTITY label "Shared &amp; stable">]>
<?publication preserve?>
<dictionary edition="2" xmlns:m="urn:header" xmlns:lxnm="http://www.lexonomy.eu/">
  <m:header>Keep this &label;</m:header>
  <section xml:lang="ar"><entry lxnm:id="33">before <lxnm:subentryParent id="50"/> after</entry>
    <!--between--><entry lxnm:id="11"><sub lxnm:id="50"><t>&label;</t><m:field><![CDATA[<xml>]]></m:field><?inside keep?></sub></entry>
  </section>
  <suffix>Keep this too</suffix>
</dictionary><!--after the root-->"""
    with closing(ops.getDB("document-roundtrip")) as db:
        ops.updateDictConfig(db, "document-roundtrip", "subbing", {"sub": {}})

        def load(data, **kwargs):
            return ops.import_dictionary(db, data, "test@lexonomy",
                                         lambda *_: None, **kwargs)

        def output(clean=False):
            return "".join(ops.export("document-roundtrip", db, ops.readDictConfigs(db), clean=clean))

        assert load(source) == 2
        archive = output()
        assert "<!DOCTYPE dictionary" in archive and "<?publication preserve?>" in archive
        assert "<!--between-->" in archive and archive.endswith("<!--after the root-->")
        assert "<![CDATA[<xml>]]>" in archive and "<?inside keep?>" in archive
        root = ElementTree.fromstring(archive)
        assert root.attrib["edition"] == "2"
        assert root.find("{urn:header}header").text == "Keep this Shared & stable"
        assert root.find("suffix").text == "Keep this too"
        assert len(root.findall(".//sub")) == 1
        assert len(root.findall(".//{http://www.lexonomy.eu/}subentryParent")) == 1
        assert [entry.attrib["{http://www.lexonomy.eu/}id"] for entry in root.findall(".//entry")] == ["33", "11"]
        assert set(tuple(row) for row in db.execute("select parent_id, child_id from sub")) == {(11, 50), (33, 50)}
        assert len(ElementTree.fromstring(output(clean=True)).findall(".//sub")) == 2
        _, _, created, _ = ops.createEntry(db, ops.readDictConfigs(db), "<entry>Added in the editor</entry>", "test@lexonomy")
        assert created
        assert ElementTree.fromstring(output()).findall("section/entry")[-1].text == "Added in the editor"

        # An archival restore is independent of extraction settings.
        ops.updateDictConfig(db, "document-roundtrip", "subbing", {})
        assert load(archive.encode(), purge_history=True) == 2
        assert set(tuple(row) for row in db.execute("select parent_id, child_id from sub")) == {(11, 50), (33, 50)}
        assert len(ElementTree.fromstring(output()).findall(".//sub")) == 1

        assert load(b"<?xml version='1.0'?><addition><note>also kept</note><entry>new</entry></addition>") == 1
        assert ElementTree.fromstring(output()).findtext("addition/note") == "also kept"
        old = output()
        bad_reference = archive.replace('id="50" title=', 'id="900" title=')
        assert bad_reference != archive
        try:
            load(bad_reference.encode(), purge_history=True)
        except ValueError as error:
            assert "missing subentry" in str(error)
        else:
            raise AssertionError("A dangling archival reference was accepted.")
        assert output() == old
        assert db.execute("pragma foreign_key_check").fetchall() == []
    print("PASS XML archives retain document structure, namespaces and shared subentry identity")
except Exception:
    failures += 1
    traceback.print_exc()

try:
    with closing(ops.getDB("document-roundtrip")) as db:
        configs = ops.readDictConfigs(db)
        id, _, success, _ = ops.createEntry(db, configs, "<entry><term>New headword</term></entry>", "test@lexonomy")
        assert success
        old_xml = db.execute("select xml from entries where id=?", (id,)).fetchone()[0]
        history_count = db.execute("select count(*) from history").fetchone()[0]
        with db:
            db.execute("update entries set needs_update=1 where id=?", (id,))
            db.execute("delete from searchables where entry_id=?", (id,))
        assert ops.reindex_entries(db, ids=[id]) == 1
        assert db.execute("select xml from entries where id=?", (id,)).fetchone()[0] == old_xml
        assert db.execute("select count(*) from history").fetchone()[0] == history_count
        assert db.execute("select txt from searchables where entry_id=? and level=2", (id,)).fetchone()[0] == "New headword"
    print("PASS Reindexing refreshes derived fields without rewriting source or history")
except Exception:
    failures += 1
    traceback.print_exc()

dictDB.close()
test_directory.cleanup()
sys.exit(bool(failures))
