#!/usr/bin/env python3
"""Publish one digest into the ai-daily GitHub Pages repo.

Usage:
  python3 scripts/publish_one.py --src ~/rss-digests/digest-YYYY-MM-DD.html

Creates/updates:
  d/YYYY-MM-DD.html
  index.html (archive listing)
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path


def build_index(repo: Path) -> None:
    ddir = repo / "d"
    ddir.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(ddir.glob("*.html")):
        # Expect YYYY-MM-DD.html
        date = p.stem
        items.append((date, p.name))

    # Newest first
    def key(t):
        try:
            return dt.date.fromisoformat(t[0])
        except Exception:
            return dt.date.min

    items.sort(key=key, reverse=True)

    lines = []
    lines.append("<!doctype html>")
    lines.append('<html lang="zh-CN">')
    lines.append("<head>")
    lines.append('  <meta charset="utf-8" />')
    lines.append('  <meta name="viewport" content="width=device-width, initial-scale=1" />')
    lines.append("  <title>AI 日报 - 归档</title>")
    lines.append("  <style>")
    lines.append("    body{font:16px/1.6 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:24px;color:#111827}")
    lines.append("    h1{margin:0 0 10px}")
    lines.append("    .muted{color:#6b7280}")
    lines.append("    ul{padding-left:18px}")
    lines.append("    li{margin:8px 0}")
    lines.append("    a{color:#4f46e5;text-decoration:none}")
    lines.append("    a:hover{text-decoration:underline}")
    lines.append("  </style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append("  <h1>AI 日报 - 历史归档</h1>")
    lines.append('  <div class="muted">这里是所有历史日报链接。最新日报会在 Discord 频道里单独推送直达链接。</div>')
    lines.append("  <ul>")
    for date, fname in items:
        lines.append(f'    <li><a href="d/{fname}">{date}</a></li>')
    lines.append("  </ul>")
    lines.append("</body>")
    lines.append("</html>")

    (repo / "index.html").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Path to digest-YYYY-MM-DD.html")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[1]
    src = Path(os.path.expanduser(args.src)).resolve()

    if not src.exists():
        raise SystemExit(f"source not found: {src}")

    date = None
    # digest-YYYY-MM-DD.html
    if src.name.startswith("digest-") and src.suffix == ".html":
        date = src.name[len("digest-") : -len(".html")]

    if not date:
        raise SystemExit("cannot infer date from filename; expected digest-YYYY-MM-DD.html")

    dst = repo / "d" / f"{date}.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())

    build_index(repo)


if __name__ == "__main__":
    main()
