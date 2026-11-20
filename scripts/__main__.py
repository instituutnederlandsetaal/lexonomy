import argparse
import os
from pathlib import Path
import subprocess
import sys

import build_docker
from checks import npm, run_checks
import release


def main():
    parser = argparse.ArgumentParser(
        prog="python scripts", description="Manage the Lexonomy checkout.",
        epilog="Run %(prog)s <command> -h for command options.",
    )
    commands = parser.add_subparsers(metavar="command")
    commands.add_parser("install-frontend", help="Install frontend dependencies from the lockfile.").set_defaults(
        run=lambda args: npm("ci"),
    )
    commands.add_parser("frontend", help="Start the local Vite dev server.").set_defaults(
        run=lambda args: npm("start"),
    )
    commands.add_parser("build-frontend", help="Build the frontend for production.").set_defaults(
        run=lambda args: npm("run", "build"),
    )
    commands.add_parser("dev", help="Start the API and Vite with Docker Compose.").set_defaults(
        run=lambda args: subprocess.run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "up", "--build"], check=True,
        ),
    )
    commands.add_parser("check", help="Run lint, type checking, and the release test suites.").set_defaults(
        run=lambda args: run_checks(),
    )
    release.add_arguments(commands.add_parser("release", help="Prepare a stable Lexonomy release."))
    build_docker.add_arguments(commands.add_parser("build-docker", help="Build a Docker image from a Git tag."))

    args = parser.parse_args()
    if not hasattr(args, "run"):
        parser.print_help()
        return
    os.chdir(Path(__file__).resolve().parents[1])
    try:
        args.run(args)
    except subprocess.CalledProcessError as error:
        print(f"{Path(error.cmd[0]).name} exited with status {error.returncode}.", file=sys.stderr)
        return error.returncode
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from None
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
