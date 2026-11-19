import concurrent.futures
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from adminscripts.setup_admin import INITIAL_ADMIN, create_initial_admin, pending_code_digest, prepare_admin_setup


class InitialAdminTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "test.sqlite"
        self.conn = sqlite3.connect(self.database)
        self.addCleanup(self.conn.close)
        self.conn.execute("CREATE TABLE users (email TEXT PRIMARY KEY, passwordHash TEXT)")
        self.config = {"admins": [INITIAL_ADMIN], "readonly": False}

    def claim(self, code):
        with closing(sqlite3.connect(self.database)) as conn:
            return create_initial_admin(conn, self.config, code, "my first admin password")

    def test_restart_rotates_pending_code_and_success_closes_setup(self):
        old_code = prepare_admin_setup(self.conn, self.config)
        code = prepare_admin_setup(self.conn, self.config)
        self.assertIsNotNone(pending_code_digest(self.conn, self.config))
        self.assertFalse(self.claim(old_code))
        self.assertFalse(create_initial_admin(self.conn, self.config, code, "short"))

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(pool.map(self.claim, [code, code]), [True, False])
        self.assertIsNone(pending_code_digest(self.conn, self.config))
        self.assertEqual(self.conn.execute("SELECT email FROM users").fetchall(), [(INITIAL_ADMIN,)])

        with self.conn:
            self.conn.execute("DELETE FROM users")
        self.assertIsNone(prepare_admin_setup(self.conn, self.config))
        self.assertFalse(self.claim(code))

    def test_existing_admin_disables_pending_setup(self):
        code = prepare_admin_setup(self.conn, self.config)
        self.config["admins"].append("operator@example.test")
        with self.conn:
            self.conn.execute("INSERT INTO users (email) VALUES ('operator@example.test')")
        self.assertIsNone(pending_code_digest(self.conn, self.config))
        self.assertFalse(self.claim(code))
        self.assertIsNone(prepare_admin_setup(self.conn, self.config))

    def test_read_only_or_root_not_configured_disables_setup(self):
        for config in ({"admins": [INITIAL_ADMIN], "readonly": True}, {"admins": [], "readonly": False}):
            self.assertIsNone(prepare_admin_setup(self.conn, config))
            self.assertIsNone(pending_code_digest(self.conn, config))


if __name__ == "__main__":
    unittest.main()
