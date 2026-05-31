#!/usr/bin/env python3
"""Audit public research repositories for READMEBuilder and LLM-readiness surfaces.

The script reads ``research_repository_audit.csv`` and checks each listed
repository through the GitHub CLI. It intentionally fails when required
surfaces are missing so the manifest can drive small, reviewable PRs.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


README_TERMS = {
    "description_or_abstract": ("description", "abstract", "overview", "summary"),
    "instructions": ("quick start", "usage", "instructions", "local run", "reproduce"),
    "authors_or_funding": ("author", "maintainer", "funding", "acknowledg"),
    "files_or_layout": ("repository layout", "file", "folder", "layout"),
    "data_or_codebook": ("data", "codebook", "variable", "workbook"),
    "script_order": ("workflow", "script", "run order", "pipeline"),
    "dependencies": ("environment", "dependencies", "requirements", "software"),
    "citation": ("citation", "cite this work", "doi"),
    "license": ("license",),
    "contact": ("contact", "maintainer"),
}


@dataclass
class Result:
    repo: str
    problems: list[str]


def run_gh(args: list[str]) -> str:
    proc = subprocess.run(
        ["gh", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout


def repo_root_names(repo: str, ref: str | None) -> set[str]:
    path = f"repos/reblocke/{repo}/contents"
    if ref:
        path = f"{path}?ref={ref}"
    payload = run_gh(["api", path])
    items = json.loads(payload)
    return {item["name"] for item in items}


def fetch_text(repo: str, path: str, ref: str | None) -> str | None:
    api_path = f"repos/reblocke/{repo}/contents/{path}"
    if ref:
        api_path = f"{api_path}?ref={ref}"
    try:
        payload = run_gh(["api", api_path])
    except RuntimeError:
        return None
    item = json.loads(payload)
    if item.get("encoding") != "base64" or "content" not in item:
        return None
    return base64.b64decode(item["content"]).decode("utf-8", errors="replace")


def has_case_insensitive(names: set[str], wanted: str) -> bool:
    wanted_lower = wanted.lower()
    return any(name.lower() == wanted_lower for name in names)


def has_license(names: set[str]) -> bool:
    return any(name.lower().startswith(("license", "licence")) for name in names)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def audit_repo(row: dict[str, str], refs: dict[str, str]) -> Result:
    repo = row["repo"]
    ref = refs.get(repo)
    problems: list[str] = []
    try:
        names = repo_root_names(repo, ref)
    except RuntimeError as exc:
        return Result(repo, [f"cannot read repository contents: {exc}"])

    if not has_case_insensitive(names, "README.md"):
        problems.append("missing root README.md")
        readme_text = ""
    else:
        readme_text = fetch_text(repo, "README.md", ref) or ""

    if row.get("doi") and not has_case_insensitive(names, "CITATION.cff"):
        problems.append("publication-linked repo missing CITATION.cff")
    if not has_license(names):
        problems.append("missing LICENSE/LICENCE file")
    if not has_case_insensitive(names, "AGENTS.md"):
        problems.append("missing AGENTS.md")

    normalized = readme_text.lower()
    for label, terms in README_TERMS.items():
        if not any(term in normalized for term in terms):
            problems.append(f"README missing READMEBuilder element: {label}")

    return Result(repo, problems)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="research_repository_audit.csv")
    parser.add_argument("--repos", nargs="*", help="Optional subset of repository names")
    parser.add_argument(
        "--ref",
        action="append",
        default=[],
        metavar="REPO=REF",
        help="Check a repository at a non-default branch or tag.",
    )
    args = parser.parse_args()
    refs: dict[str, str] = {}
    for item in args.ref:
        if "=" not in item:
            parser.error(f"--ref must be in REPO=REF form: {item}")
        repo, ref = item.split("=", 1)
        refs[repo] = ref

    rows = read_manifest(Path(args.manifest))
    if args.repos:
        wanted = set(args.repos)
        rows = [row for row in rows if row["repo"] in wanted]

    results = [audit_repo(row, refs) for row in rows]
    failing = [result for result in results if result.problems]

    for result in results:
        if result.problems:
            print(f"FAIL {result.repo}")
            for problem in result.problems:
                print(f"  - {problem}")
        else:
            print(f"PASS {result.repo}")

    print(f"\nAudited {len(results)} repositories; {len(failing)} failing.")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
