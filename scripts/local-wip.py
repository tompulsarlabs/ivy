#!/usr/bin/env python3
"""Scan local project roots for git repos and publish their WIP state to
local-wip.json so the cloud scout sees local truth (dirty trees, unpushed
commits, repos with no remote at all, misconfigured commit attribution).

Privacy: the published file identifies repos by directory basename and
remote slug only — no hostname, no filesystem paths. Those are public
identifiers already (or at worst a folder name); the machine itself stays
out of the public repo. Commit identity is therefore published as a
verdict (`author_email_ok`) rather than an address: git's invented
fallback identity is literally `user@hostname.local`, so echoing it would
leak the machine name this file is careful never to carry.

Robustness (replaces the original shell version):
- JSON is generated with the json module, never string interpolation.
- A process lock serializes scans; publication uses Git's non-force ref update.
- Registered worktrees are scanned even when they live outside the roots.
- A six-hour publication heartbeat distinguishes unchanged work from no scan.
- Publication uses a temporary clone; it never stages, rebases or pushes the
  operator's checkout. Failed publication exits nonzero and the next run rescans.
"""

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

IVY = Path(os.environ.get("IVY_DIR", Path.home() / "Build" / "ivy"))
LOCK = IVY / ".local-wip.lock"
HEARTBEAT = timedelta(hours=6)
BOT = ["-c", "user.name=ivy-bot", "-c", "user.email=bot@ivy.invalid"]
# Repository-scoped environment (git rev-parse --local-env-vars), plus the
# namespace override. `git -C` alone cannot isolate an inherited Git context.
GIT_LOCAL_ENV = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT", "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE", "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX",
    "GIT_SHALLOW_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE",
}


def git_environment(publishing=False):
    env = {key: value for key, value in os.environ.items()
           if key not in GIT_LOCAL_ENV
           and not key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    if publishing:
        # Publication is bookkeeping even when launched from a developer shell
        # with explicit author/committer overrides or dates. Scan identity checks
        # retain those overrides to report the operator's actual next author.
        for role in ("AUTHOR", "COMMITTER"):
            env[f"GIT_{role}_NAME"] = "ivy-bot"
            env[f"GIT_{role}_EMAIL"] = "bot@ivy.invalid"
            env.pop(f"GIT_{role}_DATE", None)
    return env


def git(repo, *args, publishing=False):
    """Run git in `repo`; return stdout or None on failure."""
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=60,
            env=git_environment(publishing),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def required_git(repo, *args, publishing=False):
    result = git(repo, *args, publishing=publishing)
    if result is None:
        # Do not log arguments, remote URLs or stderr: they can contain secrets.
        raise RuntimeError(f"git {args[0]} failed; snapshot not published")
    return result


def discover_repos(roots):
    """Find root checkouts and their registered, existing linked worktrees."""
    found = set()
    for root in roots:
        if not root.is_dir():
            raise RuntimeError("configured scan root unavailable; snapshot not published")
        markers = list(root.glob("*/.git")) + list(root.glob("*/*/.git"))
        if (root / ".git").exists():
            markers.append(root / ".git")
        for marker in markers:
            if not (marker.is_file() or marker.is_dir()):
                continue
            repo = marker.parent.resolve()
            found.add(repo)
            listing = required_git(repo, "worktree", "list", "--porcelain", "-z")
            for field in listing.split("\0"):
                if field.startswith("worktree "):
                    worktree = Path(field[len("worktree "):])
                    # Prunable entries left by deleted temporary worktrees are
                    # not current work. Never create them or prune Git's registry.
                    if worktree.is_dir() and (worktree / ".git").exists():
                        found.add(worktree.resolve())
    return sorted(found)


def read_roots(config_path):
    """Read local_wip.roots from config.yml.

    Deliberately parses only the one documented shape (a nested list under
    `local_wip:` / `roots:`) and fails loudly on anything else, rather than
    half-implementing YAML. If the config grows past this shape, install a
    real YAML parser and replace this function.
    """
    try:
        text = config_path.read_text()
    except OSError:
        return [Path.home() / "Build"]
    roots, in_block, in_roots = [], False, False
    for line in text.splitlines():
        if re.match(r"^local_wip:", line):
            in_block, in_roots = True, False
            continue
        if in_block and re.match(r"^\S", line):
            break
        if in_block and re.match(r"^\s+roots:", line):
            in_roots = True
            continue
        if in_roots:
            m = re.match(r"^\s+-\s+(\S+)", line)
            if m:
                roots.append(Path(os.path.expanduser(m.group(1))))
            elif line.strip():
                in_roots = False
    if in_block and not roots:
        print("local-wip: local_wip block present but no roots parsed — "
              "config.yml shape changed?", file=sys.stderr)
        sys.exit(1)
    return roots or [Path.home() / "Build"]


def next_author_email(repo):
    """The email the *next* commit in `repo` would actually be authored with.

    `git config user.email` is not enough: when no identity is configured git
    silently invents `user@host.local` at commit time, which reads as "unset"
    in config but lands in the commit object — and never counts on the graph,
    because that address can't be verified against a GitHub account. `git var`
    resolves the same fallback git itself would use, so what's reported here
    is what would really be committed.
    """
    ident = git(repo, "var", "GIT_AUTHOR_IDENT") or ""
    m = re.search(r"<([^>]*)>", ident)
    return m.group(1) if m else ""


def read_connected_emails(config_path):
    """Every address verified on the account — a commit counts if its author
    is any of them.

    Ivy checked exact equality against `commit_email` alone until 2026-09-01,
    which reported `author_email_ok: false` for repos correctly configured
    with another verified address and cost several mornings of false-alarm
    nudges. Falls back to `commit_email` if `connected_emails` is absent.
    """
    emails, in_list = [], False
    try:
        lines = config_path.read_text().splitlines()
    except OSError:
        return []
    for line in lines:
        if re.match(r"^connected_emails:\s*$", line):
            in_list = True
            continue
        if in_list:
            m = re.match(r"^\s+-\s*(\S+)", line)
            if m:
                emails.append(m.group(1))
                continue
            if line.strip() and not line.startswith((" ", "\t", "#")):
                in_list = False
    if not emails:
        for line in lines:
            m = re.match(r"^commit_email:\s*(\S+)", line)
            if m:
                emails.append(m.group(1))
                break
    return emails


def scan_repo(repo, connected_emails):
    branch = required_git(repo, "branch", "--show-current") or "(detached)"
    status = required_git(repo, "status", "--porcelain")
    dirty = len(status.splitlines())
    remotes = required_git(repo, "remote").splitlines()
    has_commits = bool(required_git(repo, "rev-parse", "--revs-only", "HEAD"))
    if not remotes:
        remote = "none"
        checkout_unpushed = int(required_git(repo, "rev-list", "--count", "HEAD")) if has_commits else 0
        unpushed = int(required_git(repo, "rev-list", "--count", "--branches", *(["HEAD"] if has_commits else [])))
    else:
        remote_name = "origin" if "origin" in remotes else remotes[0]
        url = required_git(repo, "remote", "get-url", remote_name)
        m = re.fullmatch(r"(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?", url)
        remote = m.group(1) if m else "other"
        checkout_unpushed = int(
            required_git(repo, "rev-list", "--count", "HEAD", "--not", "--remotes")
        ) if has_commits else 0
        unpushed = int(required_git(repo, "rev-list", "--count", "--branches",
                                   *(["HEAD"] if has_commits else []), "--not", "--remotes"))
    return {
        "name": repo.name,
        "remote": remote,
        "branch": branch,
        "dirty_files": dirty,
        "unpushed_commits": unpushed,
        "checkout_unpushed_commits": checkout_unpushed,
        "last_commit": required_git(repo, "log", "-1", "--format=%cs") if has_commits else "",
        # Verdicts, not addresses: git's invented fallback embeds the machine
        # hostname, and this file is published to a public repo (see Privacy).
        "author_email_ok": next_author_email(repo) in connected_emails,
        "last_commit_email_ok": (
            (git(repo, "log", "-1", "--format=%ae") or "") in connected_emails
        ),
    }


def timestamp(payload):
    try:
        value = datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00"))
        return value if value.tzinfo else None
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def should_publish(previous, payload):
    new = timestamp(payload)
    if new is None:
        raise RuntimeError("scan timestamp invalid; snapshot not published")
    if not isinstance(previous, dict):
        return True
    old = timestamp(previous)
    if old and new and old > new:
        raise RuntimeError("published snapshot is newer than this scan; rescan required")
    return (previous.get("repos") != payload["repos"] or old is None
            or new - old >= HEARTBEAT)


def publish_snapshot(payload, remote):
    """Publish only this snapshot, retrying branch races without force pushes."""
    with tempfile.TemporaryDirectory(prefix="ivy-wip-publish-") as temp:
        clone = Path(temp) / "ivy"
        required_git(Path(temp), "clone", "--quiet", "--single-branch", "--branch", "main", "--", remote, str(clone), publishing=True)
        for attempt in range(3):
            if attempt:
                required_git(clone, "fetch", "--quiet", "origin", "main", publishing=True)
                # This clone is created and owned by this invocation only.
                required_git(clone, "reset", "--hard", "--quiet", "origin/main", publishing=True)
            target = clone / "local-wip.json"
            if target.is_symlink():
                raise RuntimeError("snapshot target is a symbolic link; publication refused")
            try:
                previous = json.loads(target.read_text())
            except (OSError, ValueError):
                previous = None
            if not should_publish(previous, payload):
                return False
            target.write_text(json.dumps(payload, indent=2) + "\n")
            required_git(clone, "add", "--", "local-wip.json", publishing=True)
            required_git(clone, *BOT, "-c", "commit.gpgsign=false", "commit", "--quiet", "-m",
                         f"wip: local scan — {len(payload['repos'])} checkouts",
                         "--author=ivy-bot <bot@ivy.invalid>", "--", "local-wip.json", publishing=True)
            if git(clone, "push", "--quiet", "origin", "HEAD:refs/heads/main", publishing=True) is not None:
                return True
        raise RuntimeError("snapshot publication failed after 3 attempts; next run will rescan")


def collect_snapshot():
    config = IVY / "config.yml"
    if not config.is_file():
        raise RuntimeError("scanner configuration missing; snapshot not published")
    connected = read_connected_emails(config)
    if not connected:
        raise RuntimeError("connected identities missing; snapshot not published")
    repos = [scan_repo(repo, connected) for repo in discover_repos(read_roots(config))]
    return {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "repos": repos}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print a local snapshot; no lock, writes or network")
    args = parser.parse_args(argv)
    if args.dry_run:
        print(json.dumps(collect_snapshot(), indent=2))
        return 0
    with LOCK.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("local-wip: another scan is running")
            return 0
        payload = collect_snapshot()
        remote = required_git(IVY, "remote", "get-url", "origin")
        published = publish_snapshot(payload, remote)
        print(f"local-wip: {'published' if published else 'current'} — {len(payload['repos'])} checkouts")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError) as error:
        print(f"local-wip: {error}", file=sys.stderr)
        sys.exit(1)
