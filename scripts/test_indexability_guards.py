#!/usr/bin/env python3
"""Prove indexability guards reject representative built-site regressions."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_built_site.py"


@dataclass(frozen=True)
class Mutation:
    name: str
    expected_error: str
    apply: Callable[[Path], None]


def route_file(site: Path, route: str) -> Path:
    return site / ("index.html" if route == "/" else route.strip("/") + "/index.html")


def rewrite(path: Path, transform: Callable[[str], str]) -> None:
    before = path.read_text(encoding="utf-8")
    after = transform(before)
    if after == before:
        raise RuntimeError(f"mutation did not change {path}")
    path.write_text(after, encoding="utf-8")


def replace_once(path: Path, old: str, new: str) -> None:
    def transform(text: str) -> str:
        if old not in text:
            raise RuntimeError(f"expected text not found in {path}: {old!r}")
        return text.replace(old, new, 1)

    rewrite(path, transform)


def inject_head_meta(site: Path, route: str, meta: str) -> None:
    path = route_file(site, route)

    def transform(text: str) -> str:
        return re.sub(r"(<head(?:\s[^>]*)?>)", rf"\1\n    {meta}", text, count=1)

    rewrite(path, transform)


def remove_first_work_id(site: Path, route: str) -> None:
    path = route_file(site, route)
    rewrite(path, lambda text: re.sub(r'\sdata-work-id="[^"]+"', "", text, count=1))


def change_first_work_id(site: Path, route: str) -> None:
    path = route_file(site, route)
    rewrite(
        path,
        lambda text: re.sub(
            r'data-work-id="[^"]+"', 'data-work-id="mutated:unexpected"', text, count=1
        ),
    )


def swap_first_two_work_ids(site: Path, route: str) -> None:
    path = route_file(site, route)

    def transform(text: str) -> str:
        matches = list(re.finditer(r'data-work-id="([^"]+)"', text))
        if len(matches) < 2:
            raise RuntimeError(f"expected at least two data-work-id attributes in {path}")
        first, second = matches[0].group(1), matches[1].group(1)
        index = 0

        def swap(match: re.Match[str]) -> str:
            nonlocal index
            value = match.group(1)
            if index == 0:
                value = second
            elif index == 1:
                value = first
            index += 1
            return f'data-work-id="{value}"'

        return re.sub(r'data-work-id="([^"]+)"', swap, text)

    rewrite(path, transform)


def mutate_graph(site: Path, route: str, mutation: Callable[[dict[str, Any]], None]) -> None:
    path = route_file(site, route)
    pattern = re.compile(
        r'(<script\s+type="application/ld\+json">)(.*?)(</script>)', re.DOTALL
    )

    def transform(text: str) -> str:
        match = pattern.search(text)
        if not match:
            raise RuntimeError(f"JSON-LD block not found in {path}")
        document = json.loads(match.group(2))
        mutation(document)
        replacement = f"{match.group(1)}\n{json.dumps(document)}\n{match.group(3)}"
        return f"{text[:match.start()]}{replacement}{text[match.end():]}"

    rewrite(path, transform)


def wrong_graph_type(site: Path) -> None:
    def mutation(document: dict[str, Any]) -> None:
        page = next(node for node in document["@graph"] if node.get("@id", "").endswith("#webpage"))
        page["@type"] = "WebPage"

    mutate_graph(site, "/publications/", mutation)


def duplicate_graph_id(site: Path) -> None:
    def mutation(document: dict[str, Any]) -> None:
        graph = document["@graph"]
        person = next(node for node in graph if node.get("@type") == "Person")
        portrait = next(node for node in graph if node.get("@type") == "ImageObject")
        portrait["@id"] = person["@id"]

    mutate_graph(site, "/", mutation)


def remove_bio_incoming_links(site: Path) -> None:
    changed = 0
    for path in site.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        updated, count = re.subn(r'href="/bio/"', 'href="/work/"', text)
        if count:
            path.write_text(updated, encoding="utf-8")
            changed += count
    if not changed:
        raise RuntimeError("no /bio/ incoming links found to mutate")


def remove_topic_from_sitemap(site: Path) -> None:
    path = site / "sitemap.xml"
    rewrite(
        path,
        lambda text: re.sub(
            r"\s*<url>\s*<loc>https://reblocke\.github\.io/topics/hypercapnic-respiratory-failure/</loc>.*?</url>",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        ),
    )


def add_notice_json_ld(site: Path) -> None:
    inject_head_meta(
        site,
        "/NOTICE/",
        '<script type="application/ld+json">{"@context":"https://schema.org"}</script>',
    )


def mutations() -> list[Mutation]:
    return [
        Mutation(
            "canonical-googlebot-noindex",
            "/ has blocking robots directives",
            lambda site: inject_head_meta(site, "/", '<meta name="googlebot" content="noindex">'),
        ),
        Mutation(
            "redirect-nofollow",
            "/materials/ redirect has blocking robots directives",
            lambda site: inject_head_meta(
                site, "/materials/", '<meta name="robots" content="nofollow">'
            ),
        ),
        Mutation(
            "duplicate-canonical",
            "/bio/ has 2 canonical links",
            lambda site: inject_head_meta(
                site, "/bio/", '<link rel="canonical" href="https://reblocke.github.io/bio/">'
            ),
        ),
        Mutation(
            "wrong-title",
            "/work/ title is",
            lambda site: replace_once(
                route_file(site, "/work/"),
                "Respiratory Failure Research &amp; Software | Brian W. Locke",
                "Generic Work Page",
            ),
        ),
        Mutation(
            "wrong-description",
            "/bio/ description is",
            lambda site: replace_once(
                route_file(site, "/bio/"),
                "Biography of Brian W. Locke, MD, MSCI, an Intermountain Health pulmonary and critical care physician-scientist and University of Utah fellowship faculty member.",
                "Generic biography.",
            ),
        ),
        Mutation(
            "missing-incoming-link",
            "/bio/ has no incoming crawlable link",
            remove_bio_incoming_links,
        ),
        Mutation(
            "redirect-visible-target",
            "/materials/ redirect is missing visible href to exact target",
            lambda site: replace_once(
                route_file(site, "/materials/"),
                '<a href="/work/#software-and-repositories">',
                '<a href="/work/">',
            ),
        ),
        Mutation(
            "work-content",
            "/work/ data-work-id mismatch",
            lambda site: remove_first_work_id(site, "/work/"),
        ),
        Mutation(
            "cv-content",
            "/cv/ data-work-id mismatch",
            lambda site: remove_first_work_id(site, "/cv/"),
        ),
        Mutation(
            "publication-content",
            "/publications/ data-work-id mismatch",
            lambda site: change_first_work_id(site, "/publications/"),
        ),
        Mutation(
            "topic-order",
            "/topics/hypercapnic-respiratory-failure/ data-work-id order mismatch",
            lambda site: swap_first_two_work_ids(
                site, "/topics/hypercapnic-respiratory-failure/"
            ),
        ),
        Mutation(
            "catalog-live-link",
            "/research-repositories/ is missing curated live link",
            lambda site: replace_once(
                route_file(site, "/research-repositories/"),
                'href="https://reblocke.github.io/tcco2-accuracy/"',
                'href="https://example.invalid/tcco2-accuracy/"',
            ),
        ),
        Mutation(
            "ancillary-follow",
            "/404.html robots must contain noindex and follow",
            lambda site: replace_once(site / "404.html", "noindex,follow", "noindex"),
        ),
        Mutation("notice-json-ld", "/NOTICE/ must not contain JSON-LD", add_notice_json_ld),
        Mutation(
            "json-ld-page-type",
            "/publications/ JSON-LD page @type",
            wrong_graph_type,
        ),
        Mutation("json-ld-duplicate-id", "/ JSON-LD duplicate @ids", duplicate_graph_id),
        Mutation("sitemap-route", "sitemap route mismatch", remove_topic_from_sitemap),
        Mutation(
            "robots-disallow",
            "robots.txt contains nonempty Disallow rules",
            lambda site: rewrite(site / "robots.txt", lambda text: f"{text}\nDisallow: /work/\n"),
        ),
    ]


def run_validator(site: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--site", str(site)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        type=Path,
        default=ROOT / "_site",
        help="known-good built site copied for each mutation (default: _site)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    source_site = args.site.expanduser().resolve()
    baseline = run_validator(source_site)
    if baseline.returncode:
        print("Baseline built site did not pass validation.", file=sys.stderr)
        print(baseline.stdout, file=sys.stderr, end="")
        print(baseline.stderr, file=sys.stderr, end="")
        return 1

    failures: list[str] = []
    cases = mutations()
    for case in cases:
        with tempfile.TemporaryDirectory(prefix=f"indexability-{case.name}-") as temporary:
            mutated_site = Path(temporary) / "site"
            shutil.copytree(source_site, mutated_site)
            try:
                case.apply(mutated_site)
            except (OSError, RuntimeError, StopIteration, json.JSONDecodeError) as exc:
                failures.append(f"{case.name}: mutation setup failed: {exc}")
                continue
            result = run_validator(mutated_site)
            output = f"{result.stdout}\n{result.stderr}"
            if result.returncode == 0:
                failures.append(f"{case.name}: validator unexpectedly passed")
            elif case.expected_error not in output:
                failures.append(
                    f"{case.name}: expected {case.expected_error!r}; output was {output.strip()!r}"
                )

    if failures:
        print("\n".join(f"ERROR: {failure}" for failure in failures), file=sys.stderr)
        return 1
    print(f"Indexability guard mutations passed: {len(cases)} regressions rejected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
