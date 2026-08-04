#!/usr/bin/env python3
"""Validate built routes, anchors, canonical metadata, and local assets."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
CANONICAL = {"/", "/work/", "/cv/", "/research-repositories/"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.h1_count = 0
        self.canonical: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(str(data["id"]))
        if tag == "a" and data.get("href"):
            self.hrefs.append(str(data["href"]))
        if tag == "img":
            self.images.append(data)
        if tag == "h1":
            self.h1_count += 1
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href")


def route_file(route: str) -> Path:
    return SITE / ("index.html" if route == "/" else route.strip("/") + "/index.html")


errors: list[str] = []
pages: dict[Path, PageParser] = {}
for html in SITE.rglob("*.html"):
    parser = PageParser()
    parser.feed(html.read_text(encoding="utf-8", errors="replace"))
    pages[html] = parser
    duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
    if duplicates:
        errors.append(f"{html.relative_to(SITE)} duplicate IDs: {duplicates}")
    for image in parser.images:
        if image.get("alt") is None:
            errors.append(f"{html.relative_to(SITE)} image missing alt")
        if not image.get("width") or not image.get("height"):
            errors.append(f"{html.relative_to(SITE)} image missing explicit dimensions")

for route in CANONICAL:
    path = route_file(route)
    if not path.exists():
        errors.append(f"missing canonical route {route}")
        continue
    parser = pages[path]
    if parser.h1_count != 1:
        errors.append(f"{route} has {parser.h1_count} h1 elements")
    expected = f"https://reblocke.github.io{route}"
    if parser.canonical != expected:
        errors.append(f"{route} canonical is {parser.canonical!r}, expected {expected!r}")

for html, parser in pages.items():
    for href in parser.hrefs:
        parsed = urlparse(href)
        if parsed.scheme or parsed.netloc or href.startswith(("mailto:", "tel:")):
            continue
        target_path = unquote(parsed.path)
        if not target_path and parsed.fragment:
            target_file = html
        elif target_path.startswith("/"):
            candidate = SITE / target_path.lstrip("/")
            target_file = candidate / "index.html" if candidate.is_dir() else candidate
        else:
            target_file = (html.parent / target_path).resolve()
            if target_file.is_dir():
                target_file /= "index.html"
        if not target_file.exists():
            errors.append(f"{html.relative_to(SITE)} broken internal link {href}")
            continue
        if parsed.fragment and target_file.suffix == ".html":
            target_parser = pages.get(target_file)
            if target_parser and parsed.fragment not in target_parser.ids:
                errors.append(f"{html.relative_to(SITE)} missing anchor {href}")

sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
for forbidden in ("/materials/", "/publications/", "/talks/", "/teaching/", "/portfolio/"):
    if f"https://reblocke.github.io{forbidden}" in sitemap:
        errors.append(f"redirect route appears in sitemap: {forbidden}")

catalog = json.loads((SITE / "research-repositories.json").read_text(encoding="utf-8"))
if any(record.get("repository", "").count("/") != 1 for record in catalog):
    errors.append("invalid repository in generated catalog")

if errors:
    print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Built-site validation passed for {len(pages)} HTML files.")
