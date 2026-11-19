#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from tempfile import mkdtemp

from version import VERSION


DEV = "develop"
MAIN = "main"
MAINTENANCE = "maintenance/"
# Start from the fork's last prefixed release and skip versions used by older upstream tags.
LEGACY_TAG = "int-v1.1.3"


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def ref(name):
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", name],
        stdout=subprocess.PIPE, text=True, check=False,
    ).stdout.strip()


def ancestor(older, newer):
    result = subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], check=False)
    if result.returncode > 1:
        result.check_returncode()
    return result.returncode == 0


def require_clean():
    if git("status", "--porcelain", "--untracked-files=all") or any(
        Path(git("rev-parse", "--git-path", state)).exists()
        for state in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge",
                      "rebase-apply", "sequencer")
    ):
        raise SystemExit("Finish in-progress Git operations and clean the working tree first.")


def require_main_available():
    if f"branch refs/heads/{MAIN}" in git("worktree", "list", "--porcelain").splitlines():
        raise SystemExit(f"Switch the worktree on {MAIN} to another branch before releasing.")


def last_release(head, branch):
    tags = ["tag", "--merged", head, "--sort=-version:refname"]
    legacy_commit = ref(f"refs/tags/{LEGACY_TAG}^{{commit}}")
    if legacy_commit and ancestor(legacy_commit, head):
        # Upstream numeric tags predate the project's own release line.
        tags.extend(("--contains", legacy_commit))
    else:
        legacy_commit = ""
    for tag in git(*tags).splitlines():
        match = VERSION.fullmatch(tag)
        if match and not match[4] and branch in (DEV, f"{MAINTENANCE}{match[1]}"):
            return tag, tuple(map(int, match.groups()[:3]))
    if legacy_commit and branch in (DEV, f"{MAINTENANCE}1"):
        return LEGACY_TAG, (1, 1, 3)
    return None, (0, 0, 0)


def run_checks():
    subprocess.run(["npm", "run", "typecheck"], cwd="frontend", check=True)
    subprocess.run([sys.executable, "-m", "ruff", "check", "--select", "E9,F63,F7,F82",
                    "api", "scripts"], check=True)
    subprocess.run(["npm", "test"], cwd="frontend", check=True)
    for test in sorted(Path("api").glob("test-*.py")):
        subprocess.run([sys.executable, test.name], cwd="api", check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "scripts"], check=True)


def edit_notes(version, previous_tag, head, branch):
    editor = os.environ.get("GIT_EDITOR") or subprocess.run(
        ["git", "config", "--get", "core.editor"],
        capture_output=True, text=True, check=False,
    ).stdout.strip() or os.environ.get("VISUAL") or os.environ.get("EDITOR")
    command = shlex.split(editor or ("code --wait" if shutil.which("code") else git("var", "GIT_EDITOR")))
    if Path(command[0]).name in {"code", "code-insiders"} and not {"-w", "--wait"}.intersection(command):
        command.append("--wait")
    commits = git("log", "--reverse", "--format=- %s (%h)%n%w(0,2,2)%b", head,
                  *([f"^refs/tags/{previous_tag}"] if previous_tag else []))
    notes_path = Path("releases") / f"{version}.md"
    draft = Path(mkdtemp(prefix="lexonomy-release-")) / notes_path.name
    draft.write_text(f"# Lexonomy {version}\n\n## Fixes\n\n## Features\n\n"
                     f"## Improvements\n\n## Miscellaneous\n\n## Commits to sort\n\n{commits}\n",
                     encoding="utf-8")
    try:
        subprocess.run([*command, str(draft)], check=True)
        notes = draft.read_text(encoding="utf-8")
        if not notes.strip():
            raise SystemExit("The release notes are empty.")
        require_clean()
        if git("symbolic-ref", "--short", "HEAD") != branch or git("rev-parse", "HEAD") != head:
            raise SystemExit("The release branch changed while preparing the release.")
        if branch == DEV:
            require_main_available()
        notes_path.parent.mkdir(exist_ok=True)
        with notes_path.open("x", encoding="utf-8") as output:
            output.write(notes)
    except (Exception, SystemExit, KeyboardInterrupt):
        print(f"Release draft kept at {draft}.", file=sys.stderr)
        raise
    shutil.rmtree(draft.parent)
    return notes_path


def release(push):
    require_clean()
    if git("rev-parse", "--is-shallow-repository") == "true":
        raise SystemExit("Fetch the full Git history before preparing a release.")
    branch = git("symbolic-ref", "--short", "HEAD")
    if branch != DEV and not branch.startswith(MAINTENANCE):
        raise SystemExit(f"Run on {DEV} or {MAINTENANCE}<major>.")
    if push:
        subprocess.run(["git", "fetch", "--tags", "origin"], check=True)
    head = git("rev-parse", "HEAD")
    main = ref(f"refs/heads/{MAIN}")
    if branch == DEV:
        require_main_available()
        if not main or not ancestor(main, head):
            raise SystemExit(f"{MAIN} must exist locally and be an ancestor of {DEV}.")
    if push:
        for target in (branch, MAIN) if branch == DEV else (branch,):
            remote = ref(f"refs/remotes/origin/{target}")
            if remote and not ancestor(remote, head):
                raise SystemExit(f"Integrate origin/{target} into {branch} before releasing.")

    previous_tag, (major, minor, patch) = last_release(head, branch)
    if branch != DEV and not previous_tag:
        raise SystemExit("The maintenance branch needs a release tag for its major version.")
    bumps = {"patch": (major, minor, patch + 1), "minor": (major, minor + 1, 0)}
    if branch == DEV:
        bumps["major"] = (major + 1, 0, 0)
    bump = input(f"Bump {previous_tag or '0.0.0'} ({'/'.join(bumps)})? ").strip().lower()
    if bump not in bumps:
        raise SystemExit("No release created. Choose one of the offered increments.")
    next_version = list(bumps[bump])
    while True:
        version = ".".join(map(str, next_version))
        tag = f"refs/tags/{version}"
        if not ref(tag):
            break
        legacy = ref(f"refs/tags/{LEGACY_TAG}^{{commit}}")
        if not legacy or not ancestor(f"{tag}^{{commit}}", legacy):
            raise SystemExit(f"Tag {version} already exists.")
        print(f"Skipping upstream tag {version}.", flush=True)
        next_version[("major", "minor", "patch").index(bump)] += 1

    updates = []
    branches_to_push = [f"refs/heads/{branch}"]
    if branch == DEV and bump == "major" and previous_tag:
        maintenance = f"refs/heads/{MAINTENANCE}{major}"
        previous = git("rev-parse", f"refs/tags/{previous_tag}^{{commit}}")
        local = ref(maintenance)
        remote = ref(f"refs/remotes/origin/{MAINTENANCE}{major}") if push else ""
        for tip in (local, remote):
            if tip and not ancestor(previous, tip):
                raise SystemExit(f"{MAINTENANCE}{major} must contain {previous_tag}.")
        updates.append(f"verify {maintenance} {local}" if local else
                       f"create {maintenance} {remote or previous}")
        if not remote:
            branches_to_push.append(maintenance)

    run_checks()
    notes = edit_notes(version, previous_tag, head, branch)
    subprocess.run(["git", "add", "--", str(notes)], check=True)
    subprocess.run(["git", "commit", "-m", f"Release {version}", "--", str(notes)], check=True)
    commit = git("rev-parse", "HEAD")
    if git("rev-parse", "HEAD^") != head or git("symbolic-ref", "--short", "HEAD") != branch:
        raise SystemExit("The release branch changed before committing the release notes.")
    updates.extend((f"verify refs/heads/{branch} {commit}", f"create {tag} {commit}"))
    if branch == DEV:
        require_main_available()
        updates.append(f"update refs/heads/{MAIN} {commit} {main}")
        branches_to_push.append(f"refs/heads/{MAIN}")
    subprocess.run(["git", "update-ref", "-m", f"Release {version}", "--stdin"],
                   input="\n".join(updates) + "\n", text=True, check=True)

    push_command = ["git", "push", "--atomic", "--no-follow-tags", "origin", *branches_to_push, tag]
    print(f"Created {version} with notes at {notes}.", flush=True)
    print(shlex.join(push_command), flush=True)
    if push:
        subprocess.run(push_command, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare a stable Lexonomy release.")
    parser.add_argument("--push", action="store_true", help="Push the release refs atomically to origin.")
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parents[1])
    try:
        release(args.push)
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"Release stopped after {shlex.join(error.cmd)} failed.") from None
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("Release interrupted.") from None
