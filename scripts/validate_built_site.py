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
CANONICAL = {"/", "/bio/", "/work/", "/cv/", "/research-repositories/"}
SOCIAL_TITLES = {
    "/": "Brian W. Locke, MD, MSCI",
    "/bio/": "Biography · Brian Locke",
    "/work/": "Work · Brian Locke",
    "/cv/": "Curriculum Vitae · Brian Locke",
    "/research-repositories/": "Public Research Repositories · Brian Locke",
}
SOCIAL_IMAGE = "https://reblocke.github.io/images/social-preview.png"
SOCIAL_IMAGE_ALT = "Portrait of Brian W. Locke with his name and pulmonary and critical care research focus"
SITEMAP_URL = "https://reblocke.github.io/sitemap.xml"
EXPECTED_ICONS = [
    {"rel": "icon", "href": "/favicon.svg", "type": "image/svg+xml"},
    {"rel": "icon", "href": "/favicon.ico", "sizes": "32x32"},
    {"rel": "apple-touch-icon", "href": "/apple-touch-icon.png", "sizes": "180x180"},
]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.icons: list[dict[str, str | None]] = []
        self.h1_count = 0
        self.canonical: str | None = None
        self.meta_properties: dict[str, str] = {}
        self.meta_names: dict[str, str] = {}
        self.meta_name_counts: dict[str, int] = {}
        self.meta_http_equiv: dict[str, str] = {}

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
        if tag == "link":
            rel_tokens = set(str(data.get("rel") or "").split())
            if rel_tokens.intersection({"icon", "apple-touch-icon"}):
                self.icons.append(data)
        if tag == "meta" and data.get("property") and data.get("content"):
            self.meta_properties[str(data["property"])] = str(data["content"])
        if tag == "meta" and data.get("name") and data.get("content"):
            name = str(data["name"])
            self.meta_names[name] = str(data["content"])
            self.meta_name_counts[name] = self.meta_name_counts.get(name, 0) + 1
        if tag == "meta" and data.get("http-equiv") and data.get("content"):
            self.meta_http_equiv[str(data["http-equiv"]).lower()] = str(data["content"])


def route_file(route: str) -> Path:
    return SITE / ("index.html" if route == "/" else route.strip("/") + "/index.html")


def redirect_file(route: str) -> Path:
    relative = route.lstrip("/")
    if route.endswith("/"):
        return SITE / relative / "index.html"
    if route.endswith(".html"):
        return SITE / relative
    return SITE / f"{relative}.html"


def generated_redirects() -> dict[str, str]:
    redirects: dict[str, str] = {}
    for source in sorted((ROOT / "_generated_routes").glob("*.md")):
        text = source.read_text(encoding="utf-8")
        route_match = re.search(r"^permalink:\s*(.+?)\s*$", text, flags=re.MULTILINE)
        target_match = re.search(r"^redirect_to:\s*(.+?)\s*$", text, flags=re.MULTILINE)
        if route_match and target_match:
            redirects[route_match.group(1)] = target_match.group(1)
    return redirects


errors: list[str] = []
config_match = re.search(
    r'^google_site_verification:\s*"([A-Za-z0-9_-]+)"\s*$',
    (ROOT / "_config.yml").read_text(encoding="utf-8"),
    flags=re.MULTILINE,
)
if config_match:
    google_site_verification = config_match.group(1)
else:
    google_site_verification = ""
    errors.append("unable to read google_site_verification from _config.yml")

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
    verification_count = parser.meta_name_counts.get("google-site-verification", 0)
    if route == "/":
        if verification_count != 1:
            errors.append(
                f"{route} has {verification_count} google-site-verification tags, expected 1"
            )
        expected_names["google-site-verification"] = google_site_verification
    elif verification_count:
        errors.append(f"{route} unexpectedly contains google-site-verification")
    for name, value in expected_properties.items():
        if parser.meta_properties.get(name) != value:
            errors.append(f"{route} {name} is {parser.meta_properties.get(name)!r}, expected {value!r}")
    for name, value in expected_names.items():
        if parser.meta_names.get(name) != value:
            errors.append(f"{route} {name} is {parser.meta_names.get(name)!r}, expected {value!r}")
    if len(parser.icons) != len(EXPECTED_ICONS):
        errors.append(f"{route} has {len(parser.icons)} icon declarations, expected {len(EXPECTED_ICONS)}")
    for expected_icon in EXPECTED_ICONS:
        if not any(
            all(icon.get(key) == value for key, value in expected_icon.items())
            for icon in parser.icons
        ):
            errors.append(f"{route} is missing icon declaration {expected_icon!r}")

for route, target in generated_redirects().items():
    path = redirect_file(route)
    if not path.exists():
        errors.append(f"missing generated redirect route {route}")
        continue
    parser = pages[path]
    expected_canonical = f"https://reblocke.github.io{target.split('#', 1)[0]}"
    if parser.canonical != expected_canonical:
        errors.append(
            f"{route} canonical is {parser.canonical!r}, expected {expected_canonical!r}"
        )
    if parser.meta_names.get("robots") != "noindex":
        errors.append(f"{route} redirect is missing robots noindex")
    expected_refresh = f"0; url={target}"
    if parser.meta_http_equiv.get("refresh") != expected_refresh:
        errors.append(
            f"{route} refresh is {parser.meta_http_equiv.get('refresh')!r}, "
            f"expected {expected_refresh!r}"
        )

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

favicon_svg_path = SITE / "favicon.svg"
if not favicon_svg_path.exists():
    errors.append("built SVG favicon is missing")
else:
    favicon_svg = favicon_svg_path.read_text(encoding="utf-8", errors="replace")
    if "<svg" not in favicon_svg or "Brian Locke monogram" not in favicon_svg:
        errors.append("built SVG favicon is invalid")

touch_icon_path = SITE / "apple-touch-icon.png"
if touch_icon_path.exists():
    header = touch_icon_path.read_bytes()[:26]
    if len(header) < 26 or header[:8] != b"\x89PNG\r\n\x1a\n":
        errors.append("Apple touch icon is not a valid PNG")
    elif struct.unpack(">II", header[16:24]) != (180, 180):
        errors.append("Apple touch icon dimensions are not 180x180")
    elif header[25] != 2:
        errors.append("Apple touch icon must be an opaque RGB PNG")
else:
    errors.append("built Apple touch icon is missing")

favicon_ico_path = SITE / "favicon.ico"
if favicon_ico_path.exists():
    data = favicon_ico_path.read_bytes()
    if len(data) < 22:
        errors.append("favicon.ico is invalid")
    else:
        reserved, image_type, count = struct.unpack("<HHH", data[:6])
        entries: set[tuple[int, int]] = set()
        for index in range(count):
            offset = 6 + index * 16
            if offset + 16 > len(data):
                break
            width = data[offset] or 256
            height = data[offset + 1] or 256
            entries.add((width, height))
        if reserved != 0 or image_type != 1 or (32, 32) not in entries:
            errors.append("favicon.ico does not contain a 32x32 icon")
else:
    errors.append("built favicon.ico is missing")

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
