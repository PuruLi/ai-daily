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


BOOTSTRAP_CSS = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"


def _parse_date(s: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s)
    except Exception:
        return None


def build_index(repo: Path) -> None:
    ddir = repo / "d"
    ddir.mkdir(parents=True, exist_ok=True)

    items: list[tuple[str, str]] = []
    for p in sorted(ddir.glob("*.html")):
        # Expect YYYY-MM-DD.html
        date = p.stem
        items.append((date, p.name))

    # Newest first
    def key(t: tuple[str, str]) -> dt.date:
        d = _parse_date(t[0])
        return d if d else dt.date.min

    items.sort(key=key, reverse=True)

    latest_date = items[0][0] if items else None
    updated_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = []
    lines.append("<!doctype html>")
    lines.append('<html lang="zh-CN">')
    lines.append("<head>")
    lines.append('  <meta charset="utf-8" />')
    lines.append('  <meta name="viewport" content="width=device-width, initial-scale=1" />')
    lines.append('  <meta name="description" content="AI 日报历史归档（GitHub Pages）" />')
    lines.append("  <title>AI 日报 - 归档</title>")
    lines.append(f'  <link rel="stylesheet" href="{BOOTSTRAP_CSS}">')
    lines.append('  <link rel="stylesheet" href="assets/site.css">')
    lines.append("</head>")

    lines.append("<body>")

    # Hero
    lines.append('  <header class="hero border-bottom">')
    lines.append('    <div class="container py-5">')
    lines.append('      <div class="d-flex flex-column flex-md-row align-items-md-end justify-content-between gap-3">')
    lines.append('        <div>')
    lines.append('          <h1 class="display-6 mb-2">AI 日报 · 历史归档</h1>')
    lines.append('          <div class="small-muted">这里收录所有历史日报链接。最新日报会在 Discord 频道里单独推送直达链接。</div>')
    lines.append('        </div>')
    if latest_date:
        lines.append('        <div class="d-flex gap-2">')
        lines.append(f'          <a class="btn btn-primary" href="d/{latest_date}.html">打开最新（{latest_date}）</a>')
        lines.append('          <a class="btn btn-outline-secondary" href="#archive">查看全部</a>')
        lines.append('        </div>')
    lines.append('      </div>')
    lines.append('    </div>')
    lines.append('  </header>')

    # Main
    lines.append('  <main class="container py-4" id="archive">')
    lines.append('    <div class="row">')
    lines.append('      <div class="col-12 col-lg-10 col-xl-8 mx-auto">')

    count = len(items)
    lines.append('        <div class="card archive-card mb-4">')
    lines.append('          <div class="card-body">')
    lines.append('            <div class="d-flex flex-column flex-sm-row justify-content-between gap-2">')
    lines.append(f'              <div class="fw-semibold">共收录 {count} 篇日报</div>')
    lines.append(f'              <div class="small-muted">最后更新：{updated_at}</div>')
    lines.append('            </div>')
    lines.append('          </div>')
    lines.append('        </div>')

    if not items:
        lines.append('        <div class="alert alert-secondary">暂无归档内容。</div>')
    else:
        current_month = None
        for date_str, fname in items:
            d = _parse_date(date_str)
            month = d.strftime("%Y-%m") if d else "未知"

            if month != current_month:
                if current_month is not None:
                    lines.append("          </div>")  # close list-group
                    lines.append("        </div>")    # close month block

                current_month = month
                # Month header
                lines.append('        <div class="mb-4">')
                lines.append('          <div class="d-flex align-items-center justify-content-between mb-2">')
                lines.append(f'            <span class="badge badge-month">{month}</span>')
                lines.append('            <span class="small-muted">按日期倒序</span>')
                lines.append('          </div>')
                lines.append('          <div class="list-group shadow-sm">')

            # Item
            subtitle = "点击查看日报" if d else "（日期格式异常）"
            lines.append(
                f'            <a class="list-group-item list-group-item-action d-flex align-items-center justify-content-between" href="d/{fname}">'  # noqa: E501
            )
            lines.append("              <div>")
            lines.append(f'                <div class="fw-semibold">{date_str}</div>')
            lines.append(f'                <div class="small-muted">{subtitle}</div>')
            lines.append("              </div>")
            lines.append('              <span class="btn btn-sm btn-outline-primary">打开</span>')
            lines.append("            </a>")

        # close last opened blocks
        lines.append("          </div>")
        lines.append("        </div>")

    lines.append('        <footer class="mt-5 small-muted">')
    lines.append('          <div>托管于 GitHub Pages：<a href="https://puruli.github.io/ai-daily/">puruli.github.io/ai-daily</a></div>')
    lines.append('        </footer>')

    lines.append('      </div>')
    lines.append('    </div>')
    lines.append('  </main>')

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
