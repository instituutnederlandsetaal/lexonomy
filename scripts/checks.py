import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


def npm(*args):
    executable = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not executable:
        raise SystemExit("Install Node.js and npm to run the frontend tools.")
    subprocess.run([executable, *args], cwd="frontend", check=True)


def run_checks():
    if not shutil.which("uv"):
        raise SystemExit("Install uv to run the release checks. https://docs.astral.sh/uv/getting-started/installation/")
    npm("run", "typecheck")
    subprocess.run(["uv", "tool", "run", "ruff@0.17.5", "check", "--select", "E9,F63,F7,F82",
                    "api", "scripts"], check=True)
    npm("test")
    tests = subprocess.run(["uv", "run", "--no-project", "--python", "3.12",
                            "python", "-m", "unittest", "discover", "-s", "scripts"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    if tests.returncode:
        print(tests.stdout, end="", file=sys.stderr)
        tests.check_returncode()
    print("Release script tests passed.", flush=True)

    if os.name == "nt":
        # The backend image already builds PyICU with the required ICU libraries.
        if not shutil.which("docker"):
            raise SystemExit("Install Docker with Compose to run the API checks on Windows.")
        subprocess.run(["docker", "compose", "-f", "docker-compose.dev.yml", "run",
                        "--rm", "--no-deps", "-T", "--build", "backend", "sh", "-ec",
                        'for test in test-*.py; do python "$test"; done'], check=True)
    else:
        with TemporaryDirectory(prefix="lexonomy-checks-") as venv:
            subprocess.run(["uv", "venv", "--python", "3.12", venv], check=True)
            python = str(Path(venv) / "bin/python")
            subprocess.run(["uv", "pip", "install", "--python", python,
                            "-r", "api/requirements.txt"], check=True)
            for test in sorted(Path("api").glob("test-*.py")):
                subprocess.run([python, test.name], cwd="api", check=True)
