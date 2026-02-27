#!/usr/bin/env python3
"""Publish the newest digest HTML in a directory into this GitHub Pages repo.

- Finds latest digest-YYYY-MM-DD.html in --digest-dir (by mtime)
- Copies it to d/YYYY-MM-DD.html
- Rebuilds index.html (archive)
- Commits + pushes to origin/main
- Prints the published URL

Usage:
  python3 scripts/publish_latest.py --digest-dir ~/rss-digests

Exit codes:
  0 success (printed URL)
  2 no digest found
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

DATE_RE = re.compile(r"^digest-(\d{4}-\d{2}-\d{2})\.html$")


def sh(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest-dir", required=True)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[1]
    digest_dir = Path(os.path.expanduser(args.digest_dir)).resolve()

    if not digest_dir.exists():
        print(f"digest dir not found: {digest_dir}", file=sys.stderr)
        return 2

    candidates: list[Path] = []
    for p in digest_dir.glob("digest-*.html"):
        if DATE_RE.match(p.name):
            candidates.append(p)

    if not candidates:
        print(f"no digest files found in {digest_dir}", file=sys.stderr)
        return 2

    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    m = DATE_RE.match(latest.name)
    assert m
    date = m.group(1)

    # Update repo from origin to reduce push conflicts.
    r = sh(["git", "pull", "--rebase", "origin", "main"], cwd=repo)
    if r.returncode != 0:
        print(r.stdout)
        raise SystemExit("git pull failed")

    # Copy + rebuild index.
    from scripts.publish_one import build_index  # type: ignore

    ddir = repo / "d"
    ddir.mkdir(parents=True, exist_ok=True)
    (ddir / f"{date}.html").write_bytes(latest.read_bytes())
    build_index(repo)

    r = sh(["git", "add", "d", "index.html"], cwd=repo)
    if r.returncode != 0:
        print(r.stdout)
        raise SystemExit("git add failed")

    # If no changes, still print URL.
    r = sh(["git", "diff", "--cached", "--quiet"], cwd=repo)
    if r.returncode == 0:
        # No diff staged
        url = f"https://puruli.github.io/ai-daily/d/{date}.html"
        print(url)
        return 0

    r = sh(["git", "commit", "-m", f"Publish digest {date}"], cwd=repo)
    if r.returncode != 0:
        print(r.stdout)
        raise SystemExit("git commit failed")

    r = sh(["git", "push", "origin", "main"], cwd=repo)
    if r.returncode != 0:
        print(r.stdout)
        raise SystemExit("git push failed")

    url = f"https://puruli.github.io/ai-daily/d/{date}.html"
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
