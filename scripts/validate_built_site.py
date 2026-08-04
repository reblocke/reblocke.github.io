#!/usr/bin/env python3
"""Validate built routes, anchors, canonical metadata, and local assets."""

from __future__ import annotations

import json
import re
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
CANONICAL = {"/", "/work/", "/cv/", "/research-repositories/"}
SOCIAL_TITLES = {
    "/": "Brian W. Locke, MD, MSCI",
    "/work/": "Work · Brian Locke",
    "/cv/": "Curriculum Vitae · Brian Locke",
    "/research-repositories/": "Public Research Repositories · Brian Locke",
}
SOCIAL_IMAGE = "https://reblocke.github.io/images/social-preview.png"
SOCIAL_IMAGE_ALT = "Portrait of Brian W. Locke with his name and pulmonary and critical care research focus"
SITEMAP_URL = "https://reblocke.github.io/sitemap.xml"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.h1_count = 0
        self.canonical: str | None = None
        self.meta_properties: dict[str, str] = {}
        self.meta_names: dict[str, str] = {}

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
        if tag == "meta" and data.get("property") and data.get("content"):
            self.meta_properties[str(data["property"])] = str(data["content"])
        if tag == "meta" and data.get("name") and data.get("content"):
            self.meta_names[str(data["name"])] = str(data["content"])


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
    page_description = parser.meta_names.get("description")
    if not page_description:
        errors.append(f"{route} is missing a meta description")
        page_description = ""
    expected_properties = {
        "og:type": "website",
        "og:site_name": "Brian W. Locke",
        "og:locale": "en_US",
        "og:title": SOCIAL_TITLES[route],
        "og:description": page_description,
        "og:url": expected,
        "og:image": SOCIAL_IMAGE,
        "og:image:type": "image/png",
        "og:image:width": "1200",
        "og:image:height": "630",
        "og:image:alt": SOCIAL_IMAGE_ALT,
    }
    expected_names = {
        "twitter:card": "summary_large_image",
        "twitter:title": SOCIAL_TITLES[route],
        "twitter:description": page_description,
        "twitter:image": SOCIAL_IMAGE,
        "twitter:image:alt": SOCIAL_IMAGE_ALT,
    }
    for name, value in expected_properties.items():
        if parser.meta_properties.get(name) != value:
            errors.append(f"{route} {name} is {parser.meta_properties.get(name)!r}, expected {value!r}")
    for name, value in expected_names.items():
        if parser.meta_names.get(name) != value:
            errors.append(f"{route} {name} is {parser.meta_names.get(name)!r}, expected {value!r}")

preview_path = SITE / "images" / "social-preview.png"
if preview_path.exists():
    header = preview_path.read_bytes()[:24]
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        errors.append("social preview is not a valid PNG")
    elif struct.unpack(">II", header[16:24]) != (1200, 630):
        errors.append("social preview dimensions are not 1200x630")
    if preview_path.stat().st_size > 1_000_000:
        errors.append("social preview exceeds 1 MB")
else:
    errors.append("built social preview asset is missing")

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

sitemap = ElementTree.parse(SITE / "sitemap.xml")
sitemap_routes = {
    urlparse(location.text or "").path
    for location in sitemap.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
}
if sitemap_routes != CANONICAL:
    missing = sorted(CANONICAL - sitemap_routes)
    unexpected = sorted(sitemap_routes - CANONICAL)
    errors.append(f"sitemap route mismatch; missing={missing}, unexpected={unexpected}")

robots_path = SITE / "robots.txt"
if not robots_path.exists():
    errors.append("built robots.txt is missing")
else:
    sitemap_declarations = [
        line.strip()
        for line in robots_path.read_text(encoding="utf-8").splitlines()
        if line.strip().lower().startswith("sitemap:")
    ]
    if sitemap_declarations != [f"Sitemap: {SITEMAP_URL}"]:
        errors.append(
            "robots.txt sitemap declarations are "
            f"{sitemap_declarations!r}, expected {[f'Sitemap: {SITEMAP_URL}']!r}"
        )

catalog = json.loads((SITE / "research-repositories.json").read_text(encoding="utf-8"))
if any(record.get("repository", "").count("/") != 1 for record in catalog):
    errors.append("invalid repository in generated catalog")

if errors:
    print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Built-site validation passed for {len(pages)} HTML files.")
