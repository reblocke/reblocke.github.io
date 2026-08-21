#!/usr/bin/env python3
"""Validate built routes, indexability, structured data, content, and assets."""

from __future__ import annotations

import argparse
import csv
import json
import re
import posixpath
import struct
import subprocess
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE = ROOT / "_site"
CANONICAL_ROUTES = (
    "/",
    "/bio/",
    "/work/",
    "/publications/",
    "/topics/hypercapnic-respiratory-failure/",
    "/cv/",
    "/research-repositories/",
)
CANONICAL = set(CANONICAL_ROUTES)
SOCIAL_TITLES = {
    "/": "Brian W. Locke, MD, MSCI | Pulmonary & Critical Care Research",
    "/bio/": "Brian W. Locke, MD, MSCI | Physician-Scientist Biography",
    "/work/": "Respiratory Failure Research & Software | Brian W. Locke",
    "/publications/": "Publications | Brian W. Locke, MD, MSCI",
    "/topics/hypercapnic-respiratory-failure/": "Hypercapnic Respiratory Failure Research | Brian W. Locke",
    "/cv/": "Academic CV | Brian W. Locke, MD, MSCI",
    "/research-repositories/": "Open Research Code & Repositories | Brian W. Locke",
}
EXPECTED_DESCRIPTIONS = {
    "/": "Brian W. Locke is a pulmonary and critical care physician-scientist studying respiratory failure, clinical data, prediction, causal inference, and pragmatic trials.",
    "/bio/": "Biography of Brian W. Locke, MD, MSCI, an Intermountain Health pulmonary and critical care physician-scientist and University of Utah fellowship faculty member.",
    "/work/": "Research, publications, software, and teaching by Brian W. Locke on hypercapnic respiratory failure, respiratory measurement, clinical data, and prediction.",
    "/publications/": "Peer-reviewed publications, reviews, editorials, preprints, and scholarly products by Brian W. Locke, with DOI and PubMed links.",
    "/topics/hypercapnic-respiratory-failure/": "Research by Brian W. Locke on recognizing, measuring, and managing hypercapnic respiratory failure using clinical data, physiologic measurement, and reproducible methods.",
    "/cv/": "Academic appointments, training, funding, publications, presentations, teaching, and service for Brian W. Locke, MD, MSCI.",
    "/research-repositories/": "Public research and teaching repositories associated with Brian W. Locke, with methods, analysis languages, data-availability notes, and durable source links.",
}
SCHEMA_TYPES = {
    "/": "WebPage",
    "/bio/": "ProfilePage",
    "/work/": "CollectionPage",
    "/publications/": "CollectionPage",
    "/topics/hypercapnic-respiratory-failure/": "CollectionPage",
    "/cv/": "WebPage",
    "/research-repositories/": "CollectionPage",
}
MAIN_ENTITY_ROUTES = {"/", "/bio/"}
SOCIAL_IMAGE = "https://reblocke.github.io/images/social-preview.png"
SOCIAL_IMAGE_ALT = (
    "Portrait of Brian W. Locke with his name and pulmonary and critical care "
    "research focus"
)
SITEMAP_URL = "https://reblocke.github.io/sitemap.xml"
EXPECTED_ICONS = [
    {"rel": "icon", "href": "/favicon.svg", "type": "image/svg+xml"},
    {"rel": "icon", "href": "/favicon.ico", "sizes": "32x32"},
    {"rel": "apple-touch-icon", "href": "/apple-touch-icon.png", "sizes": "180x180"},
]
EXPECTED_CATALOG_COLUMNS = [
    "repository",
    "title",
    "artifact_type",
    "analysis_language",
    "related_doi",
    "related_pmid",
    "data_availability",
    "license_status",
    "public_url",
    "live_url",
    "live_label",
    "archived",
    "default_branch",
    "latest_release",
]
BLOCKING_ROBOTS = {"noindex", "nofollow", "none"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.links: list[dict[str, str | None]] = []
        self.images: list[dict[str, str | None]] = []
        self.icons: list[dict[str, str | None]] = []
        self.data_work_ids: list[str] = []
        self.json_ld_blocks: list[str] = []
        self.h1_count = 0
        self.title_count = 0
        self.title: str | None = None
        self.canonical: str | None = None
        self.canonical_count = 0
        self.meta_properties: dict[str, str] = {}
        self.meta_names: dict[str, str] = {}
        self.meta_name_values: dict[str, list[str]] = {}
        self.meta_name_counts: dict[str, int] = {}
        self.meta_http_equiv: dict[str, str] = {}
        self._json_ld_parts: list[str] | None = None
        self._title_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(str(data["id"]))
        if data.get("data-work-id"):
            self.data_work_ids.append(str(data["data-work-id"]))
        if tag == "a" and data.get("href"):
            self.hrefs.append(str(data["href"]))
            self.links.append(data)
        if tag == "img":
            self.images.append(data)
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.title_count += 1
            self._title_parts = []
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href")
            self.canonical_count += 1
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
            self.meta_name_values.setdefault(name.lower(), []).append(str(data["content"]))
        if tag == "meta" and data.get("http-equiv") and data.get("content"):
            self.meta_http_equiv[str(data["http-equiv"]).lower()] = str(data["content"])
        if tag == "script" and str(data.get("type") or "").lower() == "application/ld+json":
            self._json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self._json_ld_parts is not None:
            self._json_ld_parts.append(data)
        if self._title_parts is not None:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_ld_parts is not None:
            self.json_ld_blocks.append("".join(self._json_ld_parts))
            self._json_ld_parts = None
        if tag == "title" and self._title_parts is not None:
            self.title = "".join(self._title_parts).strip()
            self._title_parts = None


def route_file(site: Path, route: str) -> Path:
    return site / ("index.html" if route == "/" else route.strip("/") + "/index.html")


def redirect_file(site: Path, route: str) -> Path:
    relative = route.lstrip("/")
    if route.endswith("/"):
        return site / relative / "index.html"
    if route.endswith(".html"):
        return site / relative
    return site / f"{relative}.html"


def generated_redirects() -> dict[str, str]:
    redirects: dict[str, str] = {}
    for source in sorted((ROOT / "_generated_routes").glob("*.md")):
        text = source.read_text(encoding="utf-8")
        route_match = re.search(r"^permalink:\s*(.+?)\s*$", text, flags=re.MULTILINE)
        target_match = re.search(r"^redirect_to:\s*(.+?)\s*$", text, flags=re.MULTILINE)
        if route_match and target_match:
            redirects[route_match.group(1)] = target_match.group(1)
    return redirects


def load_yaml(path: Path) -> dict[str, Any]:
    ruby = (
        "require 'json'; require 'yaml'; "
        "data = YAML.safe_load_file(ARGV.fetch(0), aliases: false) || {}; "
        "STDOUT.write(JSON.generate(data))"
    )
    completed = subprocess.run(
        ["ruby", "-e", ruby, str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(f"unable to parse {path}: {completed.stderr.strip()}")
    loaded = json.loads(completed.stdout)
    if not isinstance(loaded, dict):
        raise RuntimeError(f"expected an object in {path}")
    return loaded


def meta_tokens(parser: PageParser, name: str) -> set[str]:
    tokens: set[str] = set()
    for content in parser.meta_name_values.get(name, []):
        tokens.update(token for token in re.split(r"[\s,]+", content.lower()) if token)
    return tokens


def blocking_robots(parser: PageParser) -> list[str]:
    blocked: list[str] = []
    for name in ("robots", "googlebot", "bingbot"):
        blocked.extend(f"{name}:{token}" for token in sorted(meta_tokens(parser, name) & BLOCKING_ROBOTS))
    return blocked


def internal_target(href: str, source_route: str) -> str | None:
    parsed = urlparse(href)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc and parsed.netloc != "reblocke.github.io":
        return None
    path = unquote(parsed.path)
    if not path:
        return source_route
    if not path.startswith("/"):
        path = posixpath.normpath(posixpath.join(source_route, path))
        if not path.startswith("/"):
            path = f"/{path}"
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return path


def reference_id(value: Any) -> str | None:
    if isinstance(value, dict) and isinstance(value.get("@id"), str):
        return value["@id"]
    return None


def compare_work_ids(
    route: str, actual: list[str], expected: list[str], errors: list[str]
) -> None:
    if actual == expected:
        return
    missing = list((Counter(expected) - Counter(actual)).elements())
    unexpected = list((Counter(actual) - Counter(expected)).elements())
    if not missing and not unexpected:
        errors.append(f"{route} data-work-id order mismatch")
    else:
        errors.append(
            f"{route} data-work-id mismatch; missing={missing}, unexpected={unexpected}"
        )


def validate_json_ld(
    route: str,
    parser: PageParser,
    person: dict[str, Any],
    errors: list[str],
) -> None:
    if len(parser.json_ld_blocks) != 1:
        errors.append(
            f"{route} has {len(parser.json_ld_blocks)} JSON-LD blocks, expected one @graph"
        )
        return
    try:
        document = json.loads(parser.json_ld_blocks[0])
    except json.JSONDecodeError as exc:
        errors.append(f"{route} JSON-LD is not parseable: {exc}")
        return
    graph = document.get("@graph") if isinstance(document, dict) else None
    context = document.get("@context") if isinstance(document, dict) else None
    if context != "https://schema.org" or not isinstance(graph, list):
        errors.append(f"{route} JSON-LD must contain one schema.org @graph")
        return
    if not all(isinstance(node, dict) for node in graph):
        errors.append(f"{route} JSON-LD @graph nodes must be objects")
        return

    schema = person.get("schema", {})
    organizations = schema.get("organizations", {})
    canonical_url = f"https://reblocke.github.io{route}"
    page_id = f"{canonical_url}#webpage"
    required_ids = {
        schema.get("website_id"),
        schema.get("person_id"),
        schema.get("portrait_id"),
        page_id,
        *(organization.get("id") for organization in organizations.values()),
    }
    node_ids = [node.get("@id") for node in graph]
    if any(not isinstance(node_id, str) for node_id in node_ids):
        errors.append(f"{route} JSON-LD every @graph node must have a string @id")
        return
    duplicates = sorted(
        node_id for node_id, count in Counter(node_ids).items() if count > 1
    )
    if duplicates:
        errors.append(f"{route} JSON-LD duplicate @ids: {duplicates}")
    missing_ids = sorted(str(node_id) for node_id in required_ids - set(node_ids))
    unexpected_ids = sorted(str(node_id) for node_id in set(node_ids) - required_ids)
    if missing_ids or unexpected_ids:
        errors.append(
            f"{route} JSON-LD node IDs mismatch; missing={missing_ids}, "
            f"unexpected={unexpected_ids}"
        )
    nodes = {str(node["@id"]): node for node in graph if isinstance(node.get("@id"), str)}

    page_node = nodes.get(page_id, {})
    if page_node.get("@type") != SCHEMA_TYPES[route]:
        errors.append(
            f"{route} JSON-LD page @type is {page_node.get('@type')!r}, "
            f"expected {SCHEMA_TYPES[route]!r}"
        )
    if page_node.get("url") != canonical_url:
        errors.append(f"{route} JSON-LD page url must equal its canonical URL")
    if reference_id(page_node.get("isPartOf")) != schema.get("website_id"):
        errors.append(f"{route} JSON-LD page isPartOf must reference #website")
    if reference_id(page_node.get("about")) != schema.get("person_id"):
        errors.append(f"{route} JSON-LD page about must reference #person")
    main_entity = reference_id(page_node.get("mainEntity"))
    if route in MAIN_ENTITY_ROUTES and main_entity != schema.get("person_id"):
        errors.append(f"{route} JSON-LD page mainEntity must reference #person")
    if route not in MAIN_ENTITY_ROUTES and page_node.get("mainEntity") is not None:
        errors.append(f"{route} JSON-LD page must not define mainEntity")

    website_node = nodes.get(str(schema.get("website_id")), {})
    if website_node.get("@type") != "WebSite":
        errors.append(f"{route} JSON-LD #website must be a WebSite")
    if reference_id(website_node.get("publisher")) != schema.get("person_id"):
        errors.append(f"{route} JSON-LD WebSite publisher must reference #person")

    person_node = nodes.get(str(schema.get("person_id")), {})
    if person_node.get("@type") != "Person":
        errors.append(f"{route} JSON-LD #person must be a Person")
    if reference_id(person_node.get("image")) != schema.get("portrait_id"):
        errors.append(f"{route} JSON-LD Person image must reference #portrait")
    if reference_id(person_node.get("worksFor")) != organizations.get("employer", {}).get("id"):
        errors.append(f"{route} JSON-LD Person worksFor must reference the employer")
    affiliation_ids = [reference_id(value) for value in person_node.get("affiliation", [])]
    expected_affiliations = [
        organizations.get("university", {}).get("id"),
        organizations.get("advisor", {}).get("id"),
    ]
    if affiliation_ids != expected_affiliations:
        errors.append(f"{route} JSON-LD Person affiliations do not match person.yml")
    identifier = person_node.get("identifier", {})
    expected_orcid_url = person.get("profiles", {}).get("orcid")
    if (
        not isinstance(identifier, dict)
        or identifier.get("@type") != "PropertyValue"
        or identifier.get("propertyID") != "ORCID"
        or identifier.get("value") != schema.get("orcid_id")
        or identifier.get("url") != expected_orcid_url
    ):
        errors.append(f"{route} JSON-LD Person ORCID identifier does not match person.yml")
    profiles = person.get("profiles", {})
    expected_same_as = [
        profiles.get("orcid"),
        profiles.get("google_scholar"),
        profiles.get("github"),
        profiles.get("linkedin"),
        profiles.get("x"),
    ]
    if person_node.get("sameAs") != expected_same_as:
        errors.append(f"{route} JSON-LD Person sameAs does not match person.yml")

    portrait_node = nodes.get(str(schema.get("portrait_id")), {})
    if portrait_node.get("@type") != "ImageObject":
        errors.append(f"{route} JSON-LD #portrait must be an ImageObject")
    for organization in organizations.values():
        node = nodes.get(str(organization.get("id")), {})
        if node.get("@type") != organization.get("type") or node.get("name") != organization.get("name"):
            errors.append(
                f"{route} JSON-LD organization {organization.get('id')} does not match person.yml"
            )


def validate(site: Path) -> list[str]:
    errors: list[str] = []
    if not site.is_dir():
        return [f"built site directory does not exist: {site}"]

    try:
        person = load_yaml(ROOT / "_data/person.yml")
    except (RuntimeError, json.JSONDecodeError) as exc:
        return [str(exc)]
    try:
        work = json.loads((ROOT / "_data/generated/work.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"unable to read generated work data: {exc}"]

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
    for html in site.rglob("*.html"):
        parser = PageParser()
        parser.feed(html.read_text(encoding="utf-8", errors="replace"))
        pages[html] = parser
        duplicates = sorted(
            value for value, count in Counter(parser.ids).items() if count > 1
        )
        if duplicates:
            errors.append(f"{html.relative_to(site)} duplicate IDs: {duplicates}")
        for image in parser.images:
            if image.get("alt") is None:
                errors.append(f"{html.relative_to(site)} image missing alt")
            if not image.get("width") or not image.get("height"):
                errors.append(f"{html.relative_to(site)} image missing explicit dimensions")

    canonical_pages: dict[str, PageParser] = {}
    canonical_titles: list[str] = []
    canonical_descriptions: list[str] = []
    for route in CANONICAL_ROUTES:
        path = route_file(site, route)
        if not path.exists():
            errors.append(f"missing canonical route {route}")
            continue
        parser = pages[path]
        canonical_pages[route] = parser
        if parser.title_count != 1 or parser.title != SOCIAL_TITLES[route]:
            errors.append(
                f"{route} title is {parser.title!r} across {parser.title_count} tags, "
                f"expected {SOCIAL_TITLES[route]!r}"
            )
        if parser.title is not None:
            canonical_titles.append(parser.title)
        if parser.h1_count != 1:
            errors.append(f"{route} has {parser.h1_count} h1 elements")
        expected = f"https://reblocke.github.io{route}"
        if parser.canonical_count != 1:
            errors.append(f"{route} has {parser.canonical_count} canonical links, expected 1")
        if parser.canonical != expected:
            errors.append(f"{route} canonical is {parser.canonical!r}, expected {expected!r}")
        blocking = blocking_robots(parser)
        if blocking:
            errors.append(f"{route} has blocking robots directives: {blocking}")
        if sum(count for name, count in parser.meta_name_counts.items() if name.lower() == "robots") > 1:
            errors.append(f"{route} has duplicate robots meta tags")
        page_description = parser.meta_names.get("description")
        if page_description != EXPECTED_DESCRIPTIONS[route]:
            errors.append(
                f"{route} description is {page_description!r}, expected {EXPECTED_DESCRIPTIONS[route]!r}"
            )
        if page_description is not None:
            canonical_descriptions.append(page_description)
        page_description = page_description or ""
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
                errors.append(
                    f"{route} {name} is {parser.meta_properties.get(name)!r}, expected {value!r}"
                )
        for name, value in expected_names.items():
            if parser.meta_names.get(name) != value:
                errors.append(
                    f"{route} {name} is {parser.meta_names.get(name)!r}, expected {value!r}"
                )
        if len(parser.icons) != len(EXPECTED_ICONS):
            errors.append(
                f"{route} has {len(parser.icons)} icon declarations, expected {len(EXPECTED_ICONS)}"
            )
        for expected_icon in EXPECTED_ICONS:
            if not any(
                all(icon.get(key) == value for key, value in expected_icon.items())
                for icon in parser.icons
            ):
                errors.append(f"{route} is missing icon declaration {expected_icon!r}")
        validate_json_ld(route, parser, person, errors)

    if len(set(canonical_titles)) != len(CANONICAL_ROUTES):
        errors.append("canonical page titles must be unique")
    if len(set(canonical_descriptions)) != len(CANONICAL_ROUTES):
        errors.append("canonical page descriptions must be unique")

    incoming: dict[str, set[str]] = {route: set() for route in CANONICAL_ROUTES}
    for source_route, parser in canonical_pages.items():
        for link in parser.links:
            rel_tokens = set(str(link.get("rel") or "").lower().split())
            if "nofollow" in rel_tokens:
                continue
            target_route = internal_target(str(link.get("href") or ""), source_route)
            if target_route in incoming and target_route != source_route:
                incoming[target_route].add(source_route)
    for route, sources in incoming.items():
        if not sources:
            errors.append(f"{route} has no incoming crawlable link from a canonical page")

    redirects = generated_redirects()
    if len(redirects) != 31:
        errors.append(f"generated redirect count is {len(redirects)}, expected 31")
    for route, target in redirects.items():
        path = redirect_file(site, route)
        if not path.exists():
            errors.append(f"missing generated redirect route {route}")
            continue
        parser = pages[path]
        expected_canonical = f"https://reblocke.github.io{target.split('#', 1)[0]}"
        if parser.canonical_count != 1:
            errors.append(f"{route} redirect has {parser.canonical_count} canonical links, expected 1")
        if parser.canonical != expected_canonical:
            errors.append(
                f"{route} canonical is {parser.canonical!r}, expected {expected_canonical!r}"
            )
        blocking = blocking_robots(parser)
        if blocking:
            errors.append(f"{route} redirect has blocking robots directives: {blocking}")
        if target not in parser.hrefs:
            errors.append(f"{route} redirect is missing visible href to exact target {target}")
        expected_refresh = f"0; url={target}"
        if parser.meta_http_equiv.get("refresh") != expected_refresh:
            errors.append(
                f"{route} refresh is {parser.meta_http_equiv.get('refresh')!r}, "
                f"expected {expected_refresh!r}"
            )

    ancillary_files = {
        "/404.html": site / "404.html",
        "/NOTICE/": route_file(site, "/NOTICE/"),
    }
    for route, path in ancillary_files.items():
        if not path.exists():
            errors.append(f"missing ancillary route {route}")
            continue
        parser = pages[path]
        tokens = meta_tokens(parser, "robots")
        if not {"noindex", "follow"}.issubset(tokens):
            errors.append(f"{route} robots must contain noindex and follow")
        if parser.json_ld_blocks:
            errors.append(f"{route} must not contain JSON-LD")

    items = work.get("items", [])
    topics = work.get("topics", [])
    expected_publications = [item["id"] for item in items if item.get("type") != "abstract"]
    if "/publications/" in canonical_pages:
        compare_work_ids(
            "/publications/",
            canonical_pages["/publications/"].data_work_ids,
            expected_publications,
            errors,
        )
    expected_work = [
        item["id"]
        for section in work.get("sections", [])
        for item in items
        if item.get("section") == section.get("key") and item.get("selected", {}).get("work")
    ]
    if "/work/" in canonical_pages:
        compare_work_ids(
            "/work/", canonical_pages["/work/"].data_work_ids, expected_work, errors
        )
    expected_cv = [
        item["id"]
        for item in items
        if item.get("type") != "abstract" and item.get("selected", {}).get("cv")
    ]
    if "/cv/" in canonical_pages:
        compare_work_ids("/cv/", canonical_pages["/cv/"].data_work_ids, expected_cv, errors)
    topic = next(
        (entry for entry in topics if entry.get("id") == "hypercapnic-respiratory-failure"),
        None,
    )
    if topic is None:
        errors.append("generated work data is missing the hypercapnic-respiratory-failure topic")
    elif "/topics/hypercapnic-respiratory-failure/" in canonical_pages:
        topic_ids = set(topic.get("item_ids", []))
        expected_topic_items = [item["id"] for item in items if item["id"] in topic_ids]
        compare_work_ids(
            "/topics/hypercapnic-respiratory-failure/",
            canonical_pages["/topics/hypercapnic-respiratory-failure/"].data_work_ids,
            expected_topic_items,
            errors,
        )

    preview_path = site / "images" / "social-preview.png"
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

    favicon_svg_path = site / "favicon.svg"
    if not favicon_svg_path.exists():
        errors.append("built SVG favicon is missing")
    else:
        favicon_svg = favicon_svg_path.read_text(encoding="utf-8", errors="replace")
        if "<svg" not in favicon_svg or "Brian Locke monogram" not in favicon_svg:
            errors.append("built SVG favicon is invalid")

    touch_icon_path = site / "apple-touch-icon.png"
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

    favicon_ico_path = site / "favicon.ico"
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
            if not target_path:
                target_file = html
            elif target_path.startswith("/"):
                candidate = site / target_path.lstrip("/")
                target_file = candidate / "index.html" if candidate.is_dir() else candidate
            else:
                target_file = (html.parent / target_path).resolve()
                if target_file.is_dir():
                    target_file /= "index.html"
            if not target_file.exists():
                errors.append(f"{html.relative_to(site)} broken internal link {href}")
                continue
            if parsed.fragment and target_file.suffix == ".html":
                target_parser = pages.get(target_file)
                if target_parser and parsed.fragment not in target_parser.ids:
                    errors.append(f"{html.relative_to(site)} missing anchor {href}")

    sitemap_path = site / "sitemap.xml"
    if not sitemap_path.exists():
        errors.append("built sitemap.xml is missing")
    else:
        try:
            sitemap = ElementTree.parse(sitemap_path)
            sitemap_routes = {
                urlparse(location.text or "").path
                for location in sitemap.findall(
                    ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                )
            }
            if sitemap_routes != CANONICAL:
                missing = sorted(CANONICAL - sitemap_routes)
                unexpected = sorted(sitemap_routes - CANONICAL)
                errors.append(
                    f"sitemap route mismatch; missing={missing}, unexpected={unexpected}"
                )
        except ElementTree.ParseError as exc:
            errors.append(f"built sitemap.xml is invalid: {exc}")

    robots_path = site / "robots.txt"
    if not robots_path.exists():
        errors.append("built robots.txt is missing")
    else:
        robots_lines = [
            line.strip() for line in robots_path.read_text(encoding="utf-8").splitlines()
        ]
        sitemap_declarations = [
            line for line in robots_lines if line.lower().startswith("sitemap:")
        ]
        if sitemap_declarations != [f"Sitemap: {SITEMAP_URL}"]:
            errors.append(
                "robots.txt sitemap declarations are "
                f"{sitemap_declarations!r}, expected {[f'Sitemap: {SITEMAP_URL}']!r}"
            )
        disallow_rules = [
            line for line in robots_lines if re.match(r"(?i)^disallow:\s*\S", line)
        ]
        if disallow_rules:
            errors.append(f"robots.txt contains nonempty Disallow rules: {disallow_rules}")

    catalog_path = site / "research-repositories.json"
    catalog: list[dict[str, Any]] = []
    if not catalog_path.exists():
        errors.append("built research-repositories.json is missing")
    else:
        try:
            loaded_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            if not isinstance(loaded_catalog, list):
                errors.append("generated catalog must be a JSON array")
            else:
                catalog = loaded_catalog
        except json.JSONDecodeError as exc:
            errors.append(f"generated catalog is invalid JSON: {exc}")
    source_repositories = {
        repository.get("repository"): repository for repository in work.get("repositories", [])
    }
    for record in catalog:
        if list(record) != EXPECTED_CATALOG_COLUMNS:
            errors.append(f"generated catalog schema mismatch for {record.get('repository')}")
        if record.get("repository", "").count("/") != 1:
            errors.append("invalid repository in generated catalog")
        if not str(record.get("public_url") or "").startswith("https://"):
            errors.append(f"{record.get('repository')} public_url must be HTTPS")
        source = source_repositories.get(record.get("repository"), {})
        if record.get("live_url") != source.get("live_url") or record.get("live_label") != source.get("live_label"):
            errors.append(f"{record.get('repository')} generated live metadata does not match work data")
        if record.get("live_url"):
            for route in ("/work/", "/research-repositories/"):
                if route in canonical_pages and record["live_url"] not in canonical_pages[route].hrefs:
                    errors.append(f"{route} is missing curated live link {record['live_url']}")

    catalog_csv_path = site / "research-repositories.csv"
    if not catalog_csv_path.exists():
        errors.append("built research-repositories.csv is missing")
    else:
        with catalog_csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            catalog_rows = list(reader)
            headers = reader.fieldnames or []
        if headers != EXPECTED_CATALOG_COLUMNS:
            errors.append(f"generated catalog CSV schema is {headers}, expected {EXPECTED_CATALOG_COLUMNS}")
        if len(catalog_rows) != len(catalog):
            errors.append("generated catalog JSON and CSV row counts differ")
        for row in catalog_rows:
            matching = next(
                (record for record in catalog if record.get("repository") == row.get("repository")),
                None,
            )
            if matching is None:
                errors.append(f"generated catalog CSV has unknown repository {row.get('repository')}")
            elif row.get("live_url", "") != (matching.get("live_url") or "") or row.get(
                "live_label", ""
            ) != (matching.get("live_label") or ""):
                errors.append(f"{row.get('repository')} JSON/CSV live metadata differs")

    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        type=Path,
        default=DEFAULT_SITE,
        help="built site directory to validate (default: _site)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    site = args.site.expanduser().resolve()
    errors = validate(site)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    page_count = sum(1 for _ in site.rglob("*.html"))
    print(f"Built-site validation passed for {page_count} HTML files in {site}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
