#!/usr/bin/python3

import os
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit
from sqlite3 import Connection
import sys
import functools
from typing import Any, TYPE_CHECKING
import ops
import re
import json
import datetime
from ops import siteconfig
import bottle
from bottle import (HTTPResponse, hook, get, post, run, error, request,
                    response, static_file, abort, redirect, install)

from ops import Configs, User
from adminscripts.setup_admin import create_initial_admin, pending_code_digest

if TYPE_CHECKING:
    request: Any
    body: Any
    response: Any

# configuration
def pathinfo_adjust_wrapper(func):
    # A wrapper for _handle() method
    @functools.wraps(func)
    def _(environ):
        environ["PATH_INFO"] = environ["PATH_INFO"].encode("utf8").decode("latin1")
        return func(environ)
    return _

app = bottle.default_app()
app._handle = pathinfo_adjust_wrapper(app._handle)
app.config['autojson'] = True
bottle.BaseRequest.MEMFILE_MAX = 100 * 1024 * 1024 #10MB upload
my_url = siteconfig["baseUrl"].split("://")[1].rstrip("/")
cgi = False
if "SERVER_NAME" in os.environ and "SERVER_PORT" in os.environ:
    my_url = os.environ["SERVER_NAME"] + ":" + os.environ["SERVER_PORT"]
    cgi = True
if "HTTPS" in os.environ and os.environ["HTTPS"] == "on":
    my_base_url = "https://" + my_url + "/"
else:
    my_base_url = "http://" + my_url + "/"

# command-line arguments (unless CGI)
if not cgi and len(sys.argv) > 1:
    if sys.argv[1] in ["-h", "--help"] or len(sys.argv) != 2:
        print("Usage: %s SERVER:PORT, which default to %s" % (sys.argv[0], my_url), file=sys.stderr)
        print(sys.argv, file=sys.stderr)
        sys.exit(1)
    my_url = sys.argv[1]

api_dir = Path(__file__).resolve().parent
frontend_dist = api_dir.parent / "frontend" / "dist"
root_path = siteconfig["rootPath"]
public_path = urlsplit(siteconfig["baseUrl"]).path or "/"


@get(root_path + "<directory:re:assets|docs|furniture>/<filename>")
def frontend_asset(directory, filename):
    cache_control = "public, max-age=31536000, immutable" if directory == "assets" else "no-cache"
    asset = static_file(filename, root=frontend_dist / directory,
                        headers={"Cache-Control": cache_control})
    return HTTPResponse(status=404) if asset.status_code == 404 else asset


@get(root_path + "version.txt")
def frontend_version():
    return static_file("version.txt", root=api_dir,
                       headers={"Cache-Control": "no-cache"})


if root_path != "/":
    @get(root_path.rstrip("/"))
    def home_with_slash():
        return redirect(public_path)


# ignore trailing slashes, urldecode cookies
@hook('before_request')
def strip_path():
    if request.path != root_path:
        request.environ["PATH_INFO"] = request.environ["PATH_INFO"].rstrip("/")
    from urllib.parse import unquote
    for c in request.cookies:
        request.cookies[c] = unquote(request.cookies[c])

# profiler
def profiler(callback):
    def wrapper(*args, **kwargs):
        if request.query.prof:
            import cProfile, pstats, io
            profile = cProfile.Profile()
            profile.enable()
        body = callback(*args, **kwargs)
        if request.query.prof:
            profile.disable()
            output = io.StringIO()
            profstats = pstats.Stats(profile, stream=output)
            output.write("<pre>")
            profstats.sort_stats('time','calls').print_stats(50)
            profstats.sort_stats('cumulative').print_stats(50)
            output.write("</pre>")
            return output.getvalue()
        return body
    return wrapper
install(profiler)

# authentication decorator
def authDict(checkRights: list[str], errorRedirect: bool=False):
    """
    Decorator factory for authenticating user access to a dictionary and verifying required rights.
    Args:
        checkRights (list[str]): List of required rights to check for the user. Available rights to check are the fields in the ConfigUsersUser dict
            - (e.g., "canEdit", "canConfig", "canUpload", "canDownload").
        errorRedirect (bool, optional): If True, redirects to the dictionary page on insufficient rights.
            If False, returns the rights result dictionary. Defaults to False.
    Raises:
        404: If the dictionary does not exist.
        Redirect: If errorRedirect is True and the user lacks required rights.
    Usage:
        - @authDict(["canEdit", "canConfig", "canUpload", "canDownload"]) before any handler
        - When used with an empty list, it checks for read access only, which is not an explicit right.
        - The decorator requires the wrapped function have a "dictID" argument.
        - The wrapped function must also accept "user", "dictDB", and "configs" parameters.
        - The database connection is automatically closed after the wrapped function executes.
        - If the wrapped function returns a generator, the connection stays open until the generator is exhausted.
    """
    
    def wrap(func):
        @functools.wraps(func)
        def wrapper_verifyLoginAndDictAccess(*args, **kwargs):
            try:
                conn = ops.getDB(kwargs["dictID"])
            except IOError:
                abort(404, "No such dictionary")
            is_generator = False
            try:
                res, configs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, conn)
                if not checkRights and res["dictAccess"] is False and not configs["publico"]["public"]:
                    if errorRedirect:
                        redirect(public_path)
                    response.status = 403
                    return {"success": False}
                for r in checkRights:
                    if not res.get(r, False):
                        if errorRedirect:
                            redirect(public_path + kwargs["dictID"])
                        else:
                            return res
                kwargs["user"] = res
                kwargs["dictDB"] = conn
                kwargs["configs"] = configs
                result = func(*args, **kwargs)
                # If the result is a generator, wrap it to defer closing the connection
                if hasattr(result, '__iter__') and hasattr(result, '__next__'):
                    is_generator = True
                    def generator_wrapper(gen, connection):
                        try:
                            yield from gen
                        finally:
                            connection.close()
                    return generator_wrapper(result, conn)
                return result
            finally:
                # Only close here if we didn't return a generator
                # (generator_wrapper's finally block will close it when exhausted)
                if not is_generator:
                    conn.close()
        return wrapper_verifyLoginAndDictAccess
    return wrap

# authentication decorator
# use @auth to check that user is authenticated
def auth(func: Any):
    """
    Decorator to verify user is logged in.
    If not logged in: redirects to the homepage ("/").
    If logged in, user is added to the keyword arguments as 'user'.
    """
    @functools.wraps(func)
    def wrapper_verifyLogin(*args, **kwargs):
        res = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
        if not res["loggedin"]:
            redirect(public_path)
        kwargs["user"] = res
        return func(*args, **kwargs)
    return wrapper_verifyLogin

# admin authentication decorator
# use @auth to check that user is authenticated and admin
# assumes that the decorated function has a "user" parameter which is used to pass the user info
def authAdmin(func: Any):
    @functools.wraps(func)
    def wrapper_verifyLoginAdmin(*args, **kwargs):
        res = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
        if not res["loggedin"] or not res["isAdmin"]:
            redirect(public_path)
        kwargs["user"] = res
        return func(*args, **kwargs)
    return wrapper_verifyLoginAdmin

#homepage
@get(root_path)
def home():
    if not (frontend_dist / "index.html").is_file():
        return HTTPResponse("Run npm run build from frontend/, or open the Vite dev server.", status=503)
    return static_file("index.html", root=frontend_dist,
                       headers={"Cache-Control": "no-cache"})

@get(siteconfig["rootPath"] + "siteconfigread.json")
def lexonomyconfig():
    with closing(ops.getMainDB()) as conn:
        setup_required = pending_code_digest(conn, siteconfig) is not None
    configData = {
        "licences": siteconfig['licences'],
        "baseUrl": siteconfig['baseUrl'],
        "setupRequired": setup_required,
    }
    if "consent" in siteconfig and siteconfig["consent"].get("terms") != "":
        configData["consent"] = siteconfig["consent"]
    return configData

@post(root_path + "initial-admin.json")
def initialize_admin():
    with closing(ops.getMainDB()) as conn:
        success = create_initial_admin(conn, siteconfig, request.forms.code, request.forms.password)
    return {"success": success}

@get(siteconfig["rootPath"] + "userdicts.json")
@auth
def listuserdicts(user: User):
    dicts = ops.getDictsByUser(user["email"])
    return {"dicts": dicts}

@get(siteconfig["rootPath"] + "<dictID>/stats.json")
@authDict(["canEdit"])
def getStats(dictID: str, user: User, dictDB: Connection, configs: Configs):
    return ops.getDictStats(dictDB)

@post(siteconfig["rootPath"] + "<dictID>/entrydelete.json")
@authDict(["canEdit"])
def entrydelete(dictID: str, user: User, dictDB: Connection, configs: Configs):
    entryID = int(request.forms.id)
    ops.deleteEntry(dictDB, configs, entryID, user["email"])
    return {"success": True, "id": entryID}

@post(siteconfig["rootPath"]+"<dictID>/entryread.json")
@authDict([])
def entryread(dictID: str, user: User, dictDB: Connection, configs: Configs):
    entryID = int(request.forms.id)
    entries = ops.readEntries(dictDB, configs, entryID, titlePlain=True)
    if not entries:
        return {"success": False, "id": entryID}
    entry = entries[0]
    render = ops.get_xslt_transformer(configs["xemplate"].get("_xsl", ""))
    return {**entry, "success": True, **ops.get_entry_rendering(dictDB, entry["xml"], render)}

def entry_save_result(dictDB, configs, id, xml, success, feedback):
    result = {"success": success, "id": id, "feedback": feedback}
    if success:
        content = str(xml)
        render = ops.get_xslt_transformer(configs["xemplate"].get("_xsl", ""))
        result.update(content=content, schemaId=ops.entry_schema_id(configs, xml),
                      **ops.get_entry_rendering(dictDB, content, render))
    return result

@post(siteconfig["rootPath"]+"<dictID>/entryupdate.json")
@authDict(["canEdit"])
def entryupdate(dictID: str, user: User, dictDB: Connection, configs: Configs):
    entryID = int(request.forms.id ) if request.forms.id else None
    saved = ops.createEntry(dictDB, configs, xml=request.forms.content, email=user["email"], id=entryID)
    return entry_save_result(dictDB, configs, *saved)

@post(siteconfig["rootPath"]+"<dictID>/entrycreate.json")
@authDict(["canEdit"])
def entrycreate(dictID: str, user: User, dictDB: Connection, configs: Configs):
    xml = request.forms.content
    try:
        xml = ops.parse(xml)
        if "lxnm:entryID" in xml.attrs: # delete id attributes so we actually get a new ID for this entry
            del xml.attrs["lxnm:entryID"]
        if "lxnm:id" in xml.attrs:
            del xml.attrs["lxnm:id"]
    except:
        return { "success": False, "feedback": "Invalid XML"}

    saved = ops.createEntry(dictDB, configs, xml, email=user["email"])
    return entry_save_result(dictDB, configs, *saved)

@post(siteconfig["rootPath"]+"<dictID>/entryflag.json")
@authDict(["canEdit"])
def entryflag(dictID: str, user: User, dictDB: Connection, configs: Configs):
    entryID = int(request.forms.id)
    xml, feedback = ops.set_entry_flag(dictDB, entryID, request.forms.flag, configs, user["email"])
    dictDB.commit()
    return {"success": feedback is None, "id": entryID, "feedback": feedback}

@get(siteconfig["rootPath"]+"<dictID>/subget")
@authDict(["canEdit"])
def subget(dictID: str, user: User, dictDB: Connection, configs: Configs):
    doctype = request.query.doctype
    schema_id = request.query.schemaId
    candidates = {
        definition for definition in configs["subbing"]
        if ops.xema_get_element_name_from_id(configs["xema"], definition) == doctype
    }
    if schema_id:
        if schema_id not in candidates:
            return {"success": False}
        candidates = {schema_id}
    if not candidates:
        return {"success": True, "total": 0, "entries": []}

    _, entry_ids = ops.searchEntries(dictDB, configs, doctype, None, request.query.lemma, "wordstart")
    entries = []
    page_size = 100
    for offset in range(0, len(entry_ids), page_size):
        for entry in ops.readEntries(dictDB, configs, entry_ids[offset:offset + page_size], tag=True, xml=False):
            tag = entry.pop("tag", None)
            definition = entry.get("schemaId")
            if tag is not None and definition in candidates and ops.is_subentry(configs["subbing"], tag, definition):
                entries.append(entry)
        if len(entries) >= page_size:
            break
    return {"success": True, "total": len(entries), "entries": entries[:page_size]}

@post(siteconfig["rootPath"]+"<dictID>/history.json")
@authDict(["canEdit"])
def history(dictID: str, dictDB: Connection, user: User, configs: Configs):
    entryID = int(request.forms.id)
    history = ops.readDictHistory(dictDB, dictID, configs, entryID)
    return {"history":history}

@post(siteconfig["rootPath"] + "consent.json")
@auth
def save_consent(user: User):
    res = ops.setConsent(user["email"], request.forms.consent)
    return {"success": res}

@post(siteconfig["rootPath"] + "login.json")
def check_login():
    email = request.forms.get("email")
    password = request.forms.get("password")
    if email is not None or password is not None:
        res = ops.login(email, password) if email and password else {"success": False}
        if res["success"]:
            #response.set_cookie("email", res["email"], path="/")
            #response.set_cookie("sessionkey", res["key"], path="/")
            response.add_header('Set-Cookie', "email=\""+res["email"]+"\"; Path=/; SameSite=None; Secure")
            response.add_header('Set-Cookie', "sessionkey="+res["key"]+"; Path=/; SameSite=None; Secure")
            return {"success": True, "email": res["email"], "sessionkey": res["key"], "consent": res["consent"]}
        return {"success": False}
    if request.cookies.email != "" and request.cookies.sessionkey != "":
        res = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
        if res["loggedin"]:
            return {"success": True, "email": res["email"], "sessionkey": request.cookies.sessionkey, "consent": res["consent"]}
    return {"success": False}

@post(siteconfig["rootPath"] + "logout.json")
@auth
def do_logout(user: User):
    ops.logout(user)
    response.delete_cookie("email", path="/")
    response.delete_cookie("sessionkey", path="/")
    return {"success": False}

@get(siteconfig["rootPath"] + "logout")
@auth
def logout(user: User):
    ops.logout(user)
    if not "Referer" in request.headers:
        referer = "/"
    elif re.search(r"/logout/$",request.headers["Referer"]):
        referer = "/"
    else:
        referer = request.headers["Referer"]
    response.delete_cookie("email", path="/")
    response.delete_cookie("sessionkey", path="/")
    return redirect(referer)

@post(siteconfig["rootPath"] + "verifytoken.json")
def verify_token():
    valid = ops.verifyToken(request.forms.token, request.forms.type)
    return {"success": valid}

@post(siteconfig["rootPath"] + "signup.json")
def send_signup():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.sendSignupToken(request.forms.email, client_ip)
    return {"success": res}

@post(siteconfig["rootPath"] + "createaccount.json")
def do_create_account():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.createAccount(request.forms.token, request.forms.password, client_ip)
    return {"success": res}

@post(siteconfig["rootPath"] + "forgotpwd.json")
def forgotpwd():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.sendToken(request.forms.email, client_ip)
    return {"success": res}

@post(siteconfig["rootPath"] + "recoverpwd.json")
def do_recover_pwd():
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    res = ops.resetPwd(request.forms.token, request.forms.password, client_ip)
    return {"success": res}

@get(siteconfig["rootPath"] + "makesuggest.json")
@auth
def makedict(user: User):
    return {"baseUrl": siteconfig['baseUrl'], "suggested": ops.suggestDictId()}

@post(siteconfig["rootPath"] + "make.json")
@auth
def makedictjson(user: User):
    dict_id = request.forms.url
    template = request.forms.template or "blank"
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", dict_id) or template not in {"blank", "smd", "sbd"}:
        return {"success": False}
    return {"success": ops.makeDict(dict_id, template, request.forms.title, "", user["email"]), "url": dict_id}

@post(siteconfig["rootPath"]+"<dictID>/clone.json")
@authDict(["canConfig"])
def clonedict(dictID: str, user: User, dictDB: Connection, configs: Configs):
    res = ops.cloneDict(dictID, user["email"])
    res["dicts"] = ops.getDictsByUser(user["email"])
    return res

@post(siteconfig["rootPath"]+"<dictID>/destroy.json")
@authDict(["canConfig"])
def destroydict(dictID: str, user: User, dictDB: Connection, configs: Configs):
    dictDB.close()
    res = ops.destroyDict(dictID)
    return {"success": res, "dicts": ops.getDictsByUser(user["email"])}

@post(siteconfig["rootPath"]+"<dictID>/move.json")
@authDict(["canConfig"])
def movedict(dictID: str, user: User, dictDB: Connection, configs: Configs):
    res = ops.moveDict(dictID, request.forms.url)
    return {"success": res}

@post(siteconfig["rootPath"] + "changepwd.json")
@auth
def changepwd(user: User):
    res = ops.changePwd(user["email"], request.forms.password)
    return {"success": res}

@post(siteconfig["rootPath"] + "users/userlist.json")
@authAdmin
def userelist(user: User):
    res = ops.listUsers(request.forms.searchtext, request.forms.howmany)
    return {"success": True, "entries": res["entries"], "total": res["total"]}

@post(siteconfig["rootPath"] + "users/userupdate.json")
@authAdmin
def userupdate(user: User):
    res = ops.updateUser(request.forms.id, request.forms.content)
    return {"success": True, "id": res["email"], "content": res["xml"]}

@post(siteconfig["rootPath"] + "users/usercreate.json")
@authAdmin
def usercreate(user: User):
    res = ops.createUser(request.forms.content)
    return {"success": True, "id": res["entryID"], "content": res["adjustedXml"]}

@post(siteconfig["rootPath"] + "users/userdelete.json")
@authAdmin
def userdelete(user: User):
    res = ops.deleteUser(request.forms.id)
    return {"success": True, "id": request.forms.id}

@post(siteconfig["rootPath"] + "users/userread.json")
@authAdmin
def userread(user: User):
    res = ops.readUser(request.forms.id)
    if res["email"] == "":
        return {"success": False}
    else:
        return {"success": True, "id": res["email"], "content": res["xml"]}

@post(siteconfig["rootPath"] + "dicts/dictlist.json")
@authAdmin
def dictlist(user: User):
    res = ops.listDicts(request.forms.searchtext, request.forms.howmany)
    return {"success": True, "entries": res["entries"], "total": res["total"]}

@post(siteconfig["rootPath"] + "dicts/dictread.json")
@authAdmin
def dictread(user: User):
    res = ops.readDict(request.forms.id)
    if res["id"] == "":
        return {"success": False}
    else:
        return {"success": True, "id": res["id"], "content": res["xml"]}

@get(siteconfig["rootPath"]+"<dictID>/config.json")
def dictconfig(dictID: str):
    if not ops.dictExists(dictID):
        return {"success": False}
    else:
        with ops.getDB(dictID) as dictDB:
            user, configs = ops.verifyLoginAndDictAccess(request.cookies.email, request.cookies.sessionkey, dictDB)
            if user["dictAccess"] is False and not configs["publico"]["public"]:
                return {"success": False}
            xema = configs["xema"]
            root_tag = ops.xema_get_element_name_from_id(xema, xema["root"])
            subentry_tags = [ops.xema_get_element_name_from_id(xema, key) for key in configs["subbing"]]
            doctypes = list(dict.fromkeys([root_tag, *subentry_tags, *ops.readDoctypesUsed(dictDB)]))
            can_author = user.get("canEdit") or user.get("canConfig")
            return {
                "success": True, "doctype": root_tag, "doctypes": doctypes, "userAccess": user["dictAccess"],
                "publicInfo": {**configs["ident"], **configs["publico"],
                               "blurb": ops.markdown_text(str(configs["ident"]["blurb"] or ""))},
                "configs": {
                    "xema": xema if can_author else {"root": xema["root"], "elements": xema["elements"]},
                    "editing": configs["editing"] if can_author else {"xonomyMode": "nerd"},
                    "metadata": configs["metadata"] if can_author else {},
                    "xemplate": configs["xemplate"], "subbing": configs["subbing"], "titling": configs["titling"],
                    "flagging": configs["flagging"], "linking": configs["links"],
                },
            }

@get(siteconfig["rootPath"]+"<dictID>/doctype.json")
@authDict([])
def dictconfig(dictID: str, user: User, dictDB: Connection, configs: Configs):
    xema = configs["xema"]
    root_tag = ops.xema_get_element_name_from_id(xema, xema["root"])
    doctypes = [root_tag, *(ops.xema_get_element_name_from_id(xema, key) for key in configs["subbing"])]
    return {"success": True, "doctype": root_tag, "doctypes": list(dict.fromkeys(doctypes)), "userAccess": user["dictAccess"]}

@get(siteconfig["rootPath"]+"<dictID>/<entryID:re:\\d+>/nabes.json")
@authDict([])
def publicentrynabes(dictID: str, entryID: int, user: User, dictDB: Connection, configs: Configs):
    nabes = ops.readNabesByEntryID(dictDB, dictID, entryID, configs)
    return {"nabes": nabes}

@get(siteconfig["rootPath"]+"<dictID>/<entryID:re:\\d+>.xml")
@authDict([], True)
def publicentryxml(dictID: str, entryID: int, user: User, dictDB: Connection, configs: Configs):
    if not configs["publico"]["public"]:
        return redirect(public_path + dictID)
    if not "licence" in configs["publico"] or not siteconfig["licences"][configs["publico"]["licence"]]["canDownloadXml"]:
        return redirect(public_path + dictID)
    res = ops.exportEntryXml(dictDB, dictID, entryID, configs, siteconfig["baseUrl"])
    if res["entryID"] == 0:
        return redirect(public_path + dictID)
    response.content_type = "text/xml; charset=utf-8"
    return res["xml"]

@post(siteconfig["rootPath"]+"<dictID>/random.json")
def publicrandom(dictID: str):
    if not ops.dictExists(dictID):
        return redirect(public_path)
    with ops.getDB(dictID) as dictDB:
        configs = ops.readDictConfigs(dictDB)
        if not configs["publico"]["public"]:
            return {"more": False, "entries": []}
        res = ops.readRandoms(dictDB)
        return res

@post(siteconfig["rootPath"]+"<dictID>/randomone.json")
@authDict(["canConfig"])
def randomone(dictID: str, user: User, dictDB: Connection, configs: Configs):
    return ops.readRandomOne(dictDB, configs)

@get(siteconfig["rootPath"]+"<dictID>/download.xml")
@authDict(["canDownload"], True)
def downloadxml(dictID: str, user: User, dictDB: Connection, configs: Configs):
    clean = False
    if request.query.clean and request.query.clean == "true":
        clean = True
    response.content_type = "text/xml; charset=utf-8"
    response.set_header("Content-Disposition", "attachment; filename="+dictID+".xml")
    return ops.export(dictID, dictDB, configs, clean)

@post(siteconfig["rootPath"]+"<dictID>/upload.html")
@authDict(["canUpload"])
def uploadhtml(dictID: str, user: User, dictDB: Connection, configs: Configs):
    import tempfile
    upload = request.files.get("myfile")
    if not upload:
        return {"success": False}

    uploads = Path(siteconfig["dataDir"]) / "uploads" / ("dictionary-" + dictID)
    uploads.mkdir(exist_ok=True)
    temppath = tempfile.mkdtemp(dir=uploads, prefix="import-")
    upload.save(temppath)
    filepath = os.path.join(temppath, upload.filename)
    ops.importfile(dictID, filepath, user["email"], purge=request.forms.purge == "on")
    return {"file": filepath, "uploadStart": str(datetime.datetime.utcnow()), "success": True}

@get(siteconfig["rootPath"]+"<dictID>/import.json")
@authDict(["canUpload"])
def importjson(dictID: str, user: User, dictDB: Connection, configs: Configs):
    uploads = Path(siteconfig["dataDir"]) / "uploads" / ("dictionary-" + dictID)
    filepath = Path(request.query.filename).resolve()
    if filepath.parent.parent != uploads or not Path(str(filepath) + ".pid.lock").is_file():
        response.status = 404
        return {"success": False}

    truncate = 0
    if request.query.truncate:
        truncate = int(request.query.truncate)
    if request.query.showErrors:
        response.content_type = "text/plain; charset=utf-8"
        response.set_header("Content-Disposition", "attachment; filename=error.log")
        return ops.showImportErrors(str(filepath), truncate)
    return ops.getImportStatus(str(filepath))

@post(siteconfig["rootPath"]+"<dictID>/<doctype>/entrylist.json")
@authDict(["canEdit"])
def entrylist(dictID: str, doctype: str, user: User, dictDB: Connection, configs: Configs):
    if request.forms.id:
        if request.forms.id == "last":
            entryID = ops.getLastEditedEntry(dictDB, user["email"])
            return {"success": True, "entryID": entryID}
        else:
            entries = ops.readEntries(dictDB, configs, int(request.forms.id))
            return {"success": True, "entries": entries}
    else:
        howmany = int(request.forms.howmany) if request.forms.howmany else 100
        offset = int(request.forms.offset) if request.forms.offset else 0
        total, entryIds = ops.searchEntries(dictDB, configs, doctype, request.forms.searchflag, request.forms.searchtext, request.forms.modifier, request.forms.sortdesc, limit = howmany, offset = offset)
        entries = ops.readEntries(dictDB, configs, entryIds, xml=False, sortdesc=request.forms.sortdesc)
        return {"success": True, "entries": entries, "total": total}

@post(siteconfig["rootPath"]+"<dictID>/search.json")
@authDict([])
def publicsearch(dictID: str, user: User, dictDB: Connection, configs: Configs):
    howmany = int(request.forms.howmany or 100)
    offset = int(request.forms.offset or 0)
    xema = configs["xema"]
    doctype = ops.xema_get_element_name_from_id(xema, xema["root"])
    total, entry_ids = ops.searchEntries(
        dictDB, configs, doctype, request.forms.searchflag, request.forms.searchtext,
        request.forms.modifier or "start", False, limit=howmany, offset=offset)
    return {"success": True, "entries": ops.readEntries(dictDB, configs, entry_ids, titlePlain=True), "total": total}


@post(siteconfig["rootPath"]+"<dictID>/configread.json")
@authDict(["canConfig"])
def configread(dictID: str, user: User, dictDB: Connection, configs: Configs):
    if request.forms.id in ops.RETIRED_DICT_CONFIGS:
        abort(404)
    config_data = configs[request.forms.id]
    if request.forms.id == 'ident':
        config_data['langs'] = ops.get_iso639_1()
    if request.forms.id == 'titling':
        config_data['locales'] = ops.get_locales()
    return {"success": True, "id": request.forms.id, "content": config_data}

@post(siteconfig["rootPath"]+"<dictID>/configupdate.json")
@authDict(["canConfig"])
def configupdate(dictID: str, user: User, dictDB: Connection, configs: Configs):
    if request.forms.id in ops.RETIRED_DICT_CONFIGS:
        abort(404)
    adjustedJson = ops.updateDictConfig(dictDB, dictID, request.forms.id, json.loads(request.forms.content))
    if request.forms.id == 'users':
        ops.notifyUsers(configs['users'], adjustedJson, configs['ident'], dictID)
        # Resaving the entries is not required here. If needed, entries have been flagged and will be updated as they are used.
    return {"success": True, "id": request.forms.id, "content": adjustedJson}

@post(siteconfig["rootPath"]+"<dictID>/autonumber.json")
@authDict(["canConfig"])
def autonumber(dictID: str, user: User, dictDB: Connection, configs: Configs):
    return ops.addAutoNumbers(dictDB, configs, user)

@post(siteconfig["rootPath"]+"<dictID>/next_autonumber.json")
@authDict(["canConfig"])
def next_autonumber(dictID: str, user: User, dictDB: Connection, configs: Configs):
    element = request.forms.element
    target = request.forms.get("target")
    return { "next": ops.get_next_autonumber_value(dictDB, element, target) }

@post(siteconfig["rootPath"]+"<dictID>/resave.json")
@authDict(["canEdit","canConfig","canUpload"])
def resavejson(dictID: str, user: User, dictDB: Connection, configs: Configs):
    ops.reindex_entries(dictDB)
    todo = ops.getDictStats(dictDB)["needUpdate"]
    return {
        "todo": todo,
        "finished": todo == 0,
        "progressMessage": f"Reindexing - {todo} entries remaining..."
    }

@get(siteconfig["rootPath"]+"publicdicts.json")
def publicdicts():
    dicts = ops.getPublicDicts()
    user = ops.verifyLogin(request.cookies.email, request.cookies.sessionkey)
    if user["loggedin"] and user["isAdmin"]:
        [dic.update({'isAdmin': True}) for dic in dicts]
    return {"entries": dicts, "success": True}

@get(siteconfig["rootPath"] + "<dictID>/links/add")
@authDict(["canEdit"])
def linksadd(dictID, user, dictDB, configs):
    source_dict = dictID
    source_el = request.query.source_el
    source_id = request.query.source_id
    target_dict = request.query.target_dict
    target_el = request.query.target_el
    target_id = request.query.target_id
    confidence = request.query.confidence
    if source_dict == "" or source_id == "" or target_dict == "" or target_id == "" or source_el == "" or target_el == "":
        return {"success": False, "error": "missing parameters"}
    else:
        res = ops.links_add(source_dict, source_el, source_id, target_dict, target_el, target_id, confidence)
        return {"success": True, "links": res}

@get(siteconfig["rootPath"] + "<dictID>/links/delete/<linkID>")
@authDict(["canEdit"])
def linksdelete(dictID, linkID, user, dictDB, configs):
    res = ops.links_delete(dictID, linkID)
    return {"success": res}

@get(siteconfig["rootPath"] + "<dictID>/links.json")
@authDict([])
def linksdict(dictID, user, dictDB, configs):
    return ops.read_dictionary_links(dictID, user)

@get(siteconfig["rootPath"] + "<dictID>/links/from")
@authDict([])
def linksfrom(dictID, user, dictDB, configs):
    source_el = request.query.source_el
    source_id = request.query.source_id
    target_dict = request.query.target_dict
    target_el = request.query.target_el
    target_id = request.query.target_id
    res = ops.links_get(dictID, source_el, source_id, target_dict, target_el, target_id, user)
    return {"links": res}

@get(siteconfig["rootPath"] + "<dictID>/links/to")
@authDict([])
def linksto(dictID, user, dictDB, configs):
    source_dict = request.query.source_dict
    source_el = request.query.source_el
    source_id = request.query.source_id
    target_el = request.query.target_el
    target_id = request.query.target_id
    res = ops.links_get(source_dict, source_el, source_id, dictID, target_el, target_id, user)
    return {"links": res}

@get(siteconfig["rootPath"]+"<dictID>/linkablelist.json")
@authDict([])
def linkablelist(dictID, user, dictDB, configs):
    res = ops.getDictLinkables(dictDB)
    return {"links": res}

@get(siteconfig["rootPath"]+"<dictID>/entrylinks.json")
@authDict([])
def entrylinks(dictID, user, dictDB, configs):
    res = ops.getEntryLinks(dictDB, dictID, request.query.id, user)
    return {"links": res}

@post(siteconfig["rootPath"] + "changefavdict.json")
@auth
def changefavdict(user):
    res = ops.changeFavDict(user['email'], request.forms.dictId, request.forms.status)
    return {"success": res}

@get(siteconfig["rootPath"]+"<dictID>")
def publicdict(dictID):
    if ops.dictExists(dictID):
        return redirect(public_path + "#" + dictID)
    else:
        return redirect(public_path)

@get(siteconfig["rootPath"]+"<dictID>/<entryID:re:\\d+>")
def publicentry(dictID, entryID):
    if ops.dictExists(dictID):
        return redirect(public_path + "#" + dictID + '/' + entryID)
    else:
        return redirect(public_path)

@get(siteconfig["rootPath"]+"<dictID>/edit")
def dictedit(dictID):
    if ops.dictExists(dictID):
        return redirect(public_path + "#" + dictID + '/edit')
    else:
        return redirect(public_path)

@get(siteconfig["rootPath"]+"<dictID>/edit/<doctype>")
def dicteditdoc(dictID, doctype):
    if ops.dictExists(dictID):
        return redirect(public_path + "#" + dictID + '/edit/' + doctype)
    else:
        return redirect(public_path)

@get(siteconfig["rootPath"]+"docs/intro")
def docintro():
    return redirect(public_path + "#docs/intro")

@error(404)
def error404(_error):
    return HTTPResponse(status=303, headers={"Location": public_path + "#/e404"})

# deployment
debug="DEBUG" in os.environ
if ":" in my_url:
    host, port = my_url.split(":")
elif siteconfig.get("port") and siteconfig["port"] > 0:
    host = my_url
    port = siteconfig["port"]
else:
    host = my_url
    port = 3000
if cgi: # we are called as CGI script
    run(host=host, port=port, debug=debug, server="cgi")
elif debug:
    run(host=host, port=port, debug=True, reloader=True, interval=0.25)
else: # run a standalone server, prefer the paste server if available over the builtin one
    try:
        import paste
        run(host=host, port=port, debug=debug, reloader=debug, server='paste', interval=0.1)
    except ImportError:
        run(host=host, port=port, debug=debug, reloader=debug, interval=0.1)

