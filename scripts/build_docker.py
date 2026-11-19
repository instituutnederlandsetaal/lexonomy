#!/usr/bin/env python3
# Retrying an older stable release can move the shorter Docker Hub tags back.
import argparse
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryFile

from version import VERSION


def build(version, push):
    match = VERSION.fullmatch(version)
    if not match or len(version) > 128:
        raise SystemExit("Use an x.y.z tag or a suffixed tag such as x.y.z-rc.1.")
    image = os.environ.get("DOCKERHUB_IMAGE", "" if push else "elexis-eu/lexonomy")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*/[a-z0-9][a-z0-9._-]*", image):
        raise SystemExit("Set DOCKERHUB_IMAGE to your Docker Hub namespace/repository.")

    revision = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"refs/tags/{version}^{{commit}}"], text=True,
    ).strip()
    message = subprocess.check_output(["git", "show", "-s", "--format=%B", revision], text=True).rstrip("\n")
    tags = [version]
    if not match[4]:
        tags.extend((f"{match[1]}.{match[2]}", match[1]))

    command = ["docker", "buildx", "build", "--target", "production",
               "--build-arg", f"VER={version}", "--build-arg", f"GIT_REVISION={revision}",
               "--build-arg", "GIT_MESSAGE"]
    command.extend(("--push", "--platform", "linux/amd64") if push else ("--load",))
    for tag in tags:
        command.extend(("--tag", f"{image}:{tag}"))
    with TemporaryFile() as context:
        subprocess.run(["git", "archive", "--format=tar", revision], stdout=context, check=True)
        context.seek(0)
        subprocess.run([*command, "-"], stdin=context, env={**os.environ, "GIT_MESSAGE": message}, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the Docker image for a Lexonomy Git tag.")
    parser.add_argument("tag", help="A local x.y.z Git tag, optionally with a suffix.")
    parser.add_argument("--push", action="store_true", help="Publish the image to Docker Hub.")
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parents[1])
    try:
        build(args.tag, args.push)
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"Docker release stopped after {error.cmd[0]} failed.") from None
