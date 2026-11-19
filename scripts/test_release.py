from contextlib import chdir
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from build_docker import build
from release import git, release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(chdir(root))
        git("init", "--initial-branch=main")
        git("config", "user.name", "Release Test")
        git("config", "user.email", "release@example.test")
        git("config", "commit.gpgsign", "false")
        git("config", "tag.gpgsign", "false")
        git("commit", "--allow-empty", "-m", "Upstream release")

    def test_major_release_and_maintenance(self):
        git("tag", "4.13.2")
        git("tag", "2.0.1")
        upstream = git("rev-parse", "2.0.1")
        git("switch", "-c", "develop")
        git("commit", "--allow-empty", "-m", "Previous project release")
        previous = git("rev-parse", "HEAD")
        git("tag", "int-v1.1.3")
        git("commit", "--allow-empty", "-m", "Add editor", "-m", "Support custom editors.")
        git("tag", "2.0.0-rc.1")
        editor = shlex.join([sys.executable, "-c",
                             "import sys; open(sys.argv[1], 'a').write('\\n- Edited release notes\\n')"])
        with TemporaryDirectory() as remote:
            git("init", "--bare", remote)
            git("remote", "add", "origin", remote)
            git("push", "origin", "main")

            with patch("release.run_checks"), patch.dict(os.environ, {"GIT_EDITOR": editor}):
                with patch("builtins.input", return_value="major"):
                    release(push=True)
                self.assertEqual(git("rev-parse", "main"), git("rev-parse", "develop"))
                self.assertEqual(git("rev-parse", "2.0.0"), git("rev-parse", "origin/main"))
                self.assertEqual(git("rev-parse", "2.0.0"), git("rev-parse", "origin/develop"))
                self.assertEqual(git("rev-parse", "origin/maintenance/1"), previous)
                notes = Path("releases/2.0.0.md").read_text()
                self.assertIn("## Improvements", notes)
                self.assertIn("Support custom editors.", notes)
                self.assertIn("Edited release notes", notes)
                self.assertNotIn("Previous project release", notes)

                git("switch", "maintenance/1")
                with patch("builtins.input", return_value="patch"):
                    release(push=True)
                self.assertEqual(git("rev-parse", "1.1.4"), git("rev-parse", "origin/maintenance/1"))
                self.assertEqual(git("rev-parse", "main"), git("rev-parse", "2.0.0"))

                git("switch", "develop")
                with patch("builtins.input", return_value="patch"):
                    release(push=True)
                self.assertEqual(git("rev-parse", "2.0.2"), git("rev-parse", "origin/main"))
                self.assertEqual(git("rev-parse", "2.0.1"), upstream)

    def test_build_uses_tagged_files_and_metadata(self):
        message = 'Add "quoted" XML\n\n<entry/> & $(nothing)'
        Path("app.txt").write_text("tagged content")
        git("add", "app.txt")
        git("commit", "-m", message)
        revision = git("rev-parse", "HEAD")
        git("tag", "2.4.6")
        git("tag", "-a", "2.4.6-rc.1", "-m", "Release candidate")
        Path("app.txt").write_text("local content")
        expected_tags = []
        real_run = subprocess.run

        def run(command, **kwargs):
            if command[0] != "docker":
                return real_run(command, **kwargs)
            self.assertEqual([command[i + 1] for i, arg in enumerate(command) if arg == "--tag"],
                             [f"test/lexonomy:{tag}" for tag in expected_tags])
            self.assertIn(f"GIT_REVISION={revision}", command)
            self.assertEqual(kwargs["env"]["GIT_MESSAGE"], message)
            with tarfile.open(fileobj=kwargs["stdin"]) as context:
                self.assertEqual(context.extractfile("app.txt").read(), b"tagged content")

        with patch.dict(os.environ, {"DOCKERHUB_IMAGE": "test/lexonomy"}), patch("subprocess.run", side_effect=run):
            expected_tags[:] = ["2.4.6", "2.4", "2"]
            build("2.4.6", push=True)
            expected_tags[:] = ["2.4.6-rc.1"]
            build("2.4.6-rc.1", push=False)
            with self.assertRaises(SystemExit):
                build("v2.4.6", push=False)
