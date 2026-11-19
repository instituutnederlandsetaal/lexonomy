import concurrent.futures
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from adminscripts.setup_admin import INITIAL_ADMIN, create_initial_admin, pending_code_digest, prepare_admin_setup
from siteconfig import find_siteconfig


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


class PasswordResetTests(unittest.TestCase):
    def test_reset_uses_api_relative_config_and_data_from_another_directory(self):
        api_dir = Path(__file__).resolve().parent
        with TemporaryDirectory() as directory:
            workdir = Path(directory)
            data_dir = workdir / "data"
            data_dir.mkdir()
            config = workdir / "override.json"
            config.write_text(json.dumps({"dataDir": os.path.relpath(data_dir, api_dir)}), encoding="utf-8")
            env = dict(os.environ, LEXONOMY_SITECONFIG=os.path.relpath(config, api_dir))
            cmd = [sys.executable, str(api_dir / "adminscripts" / "changePassword.py")]
            with closing(sqlite3.connect(data_dir / "lexonomy.sqlite")) as conn:
                with conn:
                    conn.execute("CREATE TABLE users (email TEXT PRIMARY KEY, passwordHash TEXT)")
                    conn.execute("INSERT INTO users VALUES (?, 'old')", (INITIAL_ADMIN,))

                result = subprocess.run(cmd + [INITIAL_ADMIN], cwd=workdir, env=env,
                                        capture_output=True, text=True, check=True)
                password = result.stdout.strip().rsplit(" ", 1)[-1]
                self.assertGreaterEqual(len(password), 12)
                self.assertEqual(conn.execute("SELECT passwordHash FROM users").fetchone(),
                                 (hashlib.sha1(password.encode()).hexdigest(),))

                result = subprocess.run(cmd + ["missing@example.test"], cwd=workdir, env=env,
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("No Lexonomy account found", result.stderr)


class SiteConfigTests(unittest.TestCase):
    def test_config_precedence_with_source_and_container_defaults(self):
        with TemporaryDirectory() as directory, patch.dict(os.environ, clear=True):
            root = Path(directory)
            api_dir = root / "api"
            api_dir.mkdir()
            config_dir = root / "config"
            config_dir.mkdir()
            with patch("siteconfig.API_DIR", api_dir):
                self.assertEqual(find_siteconfig(), config_dir / "siteconfig.example.json")

                bundled = root / "siteconfig.example.json"
                bundled.touch()
                self.assertEqual(find_siteconfig(), bundled)

                legacy = api_dir / "siteconfig.json"
                legacy.touch()
                self.assertEqual(find_siteconfig(), legacy)

                os.environ["LEXONOMY_SITECONFIG_FALLBACK"] = str(bundled)
                self.assertEqual(find_siteconfig(), bundled)

                mounted = config_dir / "siteconfig.json"
                mounted.touch()
                self.assertEqual(find_siteconfig(), mounted)

                os.environ["LEXONOMY_SITECONFIG"] = "missing.json"
                self.assertEqual(find_siteconfig(), api_dir / "missing.json")


if __name__ == "__main__":
    unittest.main()
