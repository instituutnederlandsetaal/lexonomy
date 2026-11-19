import hashlib
import secrets

INITIAL_ADMIN = "root@localhost"


def has_admin(conn, config):
    admins = config["admins"]
    placeholders = ",".join("?" for _ in admins)
    return bool(admins and conn.execute(
        f"SELECT 1 FROM users WHERE email IN ({placeholders}) LIMIT 1", admins
    ).fetchone())


def prepare_admin_setup(conn, config):
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS initial_admin_setup (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                code_digest TEXT
            )
        """)
        if has_admin(conn, config):
            conn.execute("INSERT OR REPLACE INTO initial_admin_setup VALUES (1, NULL)")
            return None
        if config["readonly"] or INITIAL_ADMIN not in config["admins"]:
            return None
        state = conn.execute("SELECT code_digest FROM initial_admin_setup WHERE id = 1").fetchone()
        if state is not None and state[0] is None:
            return None

        code = secrets.token_urlsafe(32)
        conn.execute("INSERT OR REPLACE INTO initial_admin_setup VALUES (1, ?)",
                     (hashlib.sha256(code.encode()).hexdigest(),))
        return code


def pending_code_digest(conn, config):
    if config["readonly"] or INITIAL_ADMIN not in config["admins"] or has_admin(conn, config):
        return None
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'initial_admin_setup'"
    ).fetchone():
        return None
    state = conn.execute("SELECT code_digest FROM initial_admin_setup WHERE id = 1").fetchone()
    return state[0] if state else None


def create_initial_admin(conn, config, code, password):
    if len(code) != 43 or not 12 <= len(password) <= 1024:
        return False
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        expected = pending_code_digest(conn, config)
        if not expected or not secrets.compare_digest(expected, hashlib.sha256(code.encode()).hexdigest()):
            return False
        conn.execute("INSERT INTO users (email, passwordHash) VALUES (?, ?)",
                     (INITIAL_ADMIN, hashlib.sha1(password.encode()).hexdigest()))
        conn.execute("UPDATE initial_admin_setup SET code_digest = NULL WHERE id = 1")
        return True
