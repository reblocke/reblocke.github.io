#!/usr/bin/env python3
"""Inventory public repository documentation surfaces without certifying readiness.

The script reads ``research-repositories.csv`` through the GitHub CLI. Keyword
matches and file presence are structural observations; semantic and scientific
review remain not_evaluated.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit


README_TERMS = {
    "description_or_abstract": (
        "description",
        "abstract",
        "overview",
        "summary",
        "purpose",
        "project summary",
    ),
    "instructions": (
        "quick start",
        "usage",
        "instructions",
        "local run",
        "reproduce",
        "workflow",
        "run from",
        "run the",
    ),
    "authors_or_funding": ("author", "maintainer", "funding", "acknowledg"),
    "files_or_layout": (
        "repository layout",
        "repository contents",
        "repository structure",
        "file",
        "folder",
        "layout",
    ),
    "data_or_codebook": ("data", "codebook", "variable", "workbook"),
    "script_order": ("workflow", "script", "run order", "pipeline"),
    "dependencies": (
        "environment",
        "dependencies",
        "requirements",
        "software",
        "install",
        "packages",
    ),
    "citation": ("citation", "cite this work", "doi"),
    "license": ("license",),
    "contact": ("contact", "maintainer"),
}

STALE_README_PATTERNS = {
    "stale LLM appendix heading": re.compile(
        r"(?im)^#{1,3}\s+LLM and Repository Readiness Notes\s*$"
    ),
    "variant LLM readiness appendix heading": re.compile(
        r"(?im)^#{1,3}\s+.*LLM.*(?:Repository\s+)?Readiness.*$"
    ),
}

README_PLACEHOLDERS = {
    "placeholder license status": "License status: CHECK",
    "placeholder citation status": "CITATION status: CHECK",
    "placeholder manuscript status": "Manuscript status: CHECK",
}


@dataclass
class Result:
    repo: str
    problems: list[str]
    readme_present: bool = False
    llms_present: bool = False
    stale_readme_hit: bool = False
    placeholder_hit: bool = False
    snapshot_sha: str = ""
    readme_path: str = ""
    readme_outcome: str = "unavailable"
    role: str = "unknown"
    semantic_review: str = "not_evaluated"
    structural_terms: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class TextRead:
    outcome: str
    text: str = ""
    detail: str = ""


@dataclass(frozen=True)
class Snapshot:
    sha: str
    tree_sha: str


@dataclass(frozen=True)
class TreeRead:
    outcome: str
    paths: frozenset[str] = frozenset()
    detail: str = ""


class GhError(RuntimeError):
    """Keep the GitHub status class available to callers."""


SUPPORTED_ROLES = frozenset(
    {
        "active research code",
        "research code",
        "reproducible analysis",
        "legacy analysis code",
        "systematic review and meta-analysis",
        "statistical visualization tool",
        "teaching site",
        "educational evaluation",
    }
)


def run_gh(args: list[str]) -> str:
    proc = subprocess.run(
        ["gh", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise GhError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout


def resolve_snapshot(repo: str, ref: str | None) -> Snapshot:
    if ref is None:
        metadata = json.loads(run_gh(["api", f"repos/reblocke/{repo}"]))
        ref = metadata["default_branch"]
    commit = json.loads(
        run_gh(["api", f"repos/reblocke/{repo}/commits/{quote(ref, safe='')}"])
    )
    sha = commit.get("sha", "")
    tree_sha = commit.get("commit", {}).get("tree", {}).get("sha", "")
    if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (sha, tree_sha)):
        raise ValueError("GitHub did not return immutable commit/tree SHAs")
    return Snapshot(sha, tree_sha)


def repo_root_names(repo: str, ref: str) -> set[str]:
    path = f"repos/reblocke/{repo}/contents"
    path = f"{path}?ref={ref}"
    payload = run_gh(["api", path])
    items = json.loads(payload)
    if not isinstance(items, list):
        raise ValueError("root contents response was not a file list")
    return {item["name"] for item in items}


def fetch_text(repo: str, path: str, ref: str) -> TextRead:
    api_path = f"repos/reblocke/{repo}/contents/{quote(path, safe='')}?ref={ref}"
    try:
        payload = run_gh(["api", api_path])
    except GhError as exc:
        detail = str(exc)
        if "HTTP 401" in detail or "HTTP 403" in detail:
            return TextRead("denied", detail=detail)
        if "HTTP 404" in detail:
            return TextRead("unavailable", detail="ambiguous 404 for discovered path")
        return TextRead("failed", detail=detail)
    try:
        item = json.loads(payload)
    except ValueError:
        return TextRead("failed", detail="invalid GitHub content response")
    if (
        not isinstance(item, dict)
        or item.get("encoding") != "base64"
        or not isinstance(item.get("content"), str)
    ):
        return TextRead("unsupported", detail="content encoding is not base64")
    try:
        text = base64.b64decode("".join(item["content"].split()), validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeError):
        return TextRead("unsupported", detail="content is not valid base64 UTF-8")
    return TextRead("ok", text=text)


def fetch_tree(repo: str, snapshot: Snapshot) -> TreeRead:
    try:
        payload = run_gh(
            ["api", f"repos/reblocke/{repo}/git/trees/{snapshot.tree_sha}?recursive=1"]
        )
        tree = json.loads(payload)
    except (GhError, ValueError) as exc:
        return TreeRead("unavailable", detail=str(exc))
    if not isinstance(tree, dict) or tree.get("truncated") or not isinstance(tree.get("tree"), list):
        return TreeRead("unsupported", detail="tracked tree incomplete")
    try:
        paths = frozenset(item["path"] for item in tree["tree"])
    except (KeyError, TypeError):
        return TreeRead("unsupported", detail="tracked tree entries malformed")
    return TreeRead("ok", paths)


def linked_source_paths(readme: str) -> set[str]:
    """Find common inline and reference links to local tracked-code locations."""
    paths: set[str] = set()
    definitions = {
        label.casefold(): angle or bare
        for label, angle, bare in re.findall(
            r"(?m)^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))",
            readme,
        )
    }
    raw_links = re.findall(r"\]\(([^)]+)\)", readme)
    raw_links.extend(
        definitions[label.casefold()]
        for label in re.findall(r"\]\[([^\]]+)\]", readme)
        if label.casefold() in definitions
    )
    for raw in raw_links:
        target = raw.strip()
        if target.startswith("<") and ">" in target:
            target = target[1 : target.index(">")]
        else:
            target = target.split()[0]
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        path = unquote(parsed.path.removeprefix("/").removeprefix("./"))
        parts = PurePosixPath(path).parts
        if not parts or ".." in parts:
            continue
        if path.startswith(("scripts/", "src/", "stata/do/", "r/scripts/", "tests/")) or (
            PurePosixPath(path).suffix.lower() in {".py", ".r", ".do", ".sh", ".ipynb", ".jl", ".sas"}
            and not path.startswith(("data/", "reports/", "docs/"))
        ):
            paths.add(path.rstrip("/"))
    return paths


def has_case_insensitive(names: set[str], wanted: str) -> bool:
    wanted_lower = wanted.lower()
    return any(name.lower() == wanted_lower for name in names)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def error_outcome(exc: Exception) -> str:
    detail = str(exc)
    if "HTTP 401" in detail or "HTTP 403" in detail:
        return "denied"
    if "HTTP 404" in detail:
        return "unavailable"
    return "failed"


def audit_repo(row: dict[str, str], refs: dict[str, str]) -> Result:
    full_name = row.get("repository") or row.get("repo") or ""
    repo = full_name.split("/", 1)[-1]
    ref = refs.get(repo)
    problems: list[str] = []
    declared_role = (row.get("artifact_type") or "").strip()
    role = declared_role if declared_role in SUPPORTED_ROLES else "unknown"
    observations: list[str] = []
    if role == "unknown":
        observations.append("manifest role is unknown; no role-specific requirements applied")
    try:
        snapshot = resolve_snapshot(repo, ref)
    except (GhError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return Result(
            repo, [f"cannot resolve repository snapshot: {exc}"],
            role=role, readme_outcome=error_outcome(exc),
        )
    try:
        names = repo_root_names(repo, snapshot.sha)
    except (GhError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return Result(
            repo, [f"cannot read repository tree: {exc}"],
            role=role, snapshot_sha=snapshot.sha, readme_outcome=error_outcome(exc),
        )

    variants = sorted(name for name in names if name.casefold() == "readme.md")
    if not variants:
        problems.append("missing root README.md")
        readme_text = ""
        readme_present = False
        readme_path = ""
        readme_outcome = "missing"
    elif len(variants) > 1:
        problems.append("ambiguous root README filename variants: " + ", ".join(variants))
        readme_text = ""
        readme_present = True
        readme_path = ""
        readme_outcome = "ambiguous"
    else:
        readme_path = variants[0]
        read = fetch_text(repo, readme_path, snapshot.sha)
        readme_text = read.text
        readme_present = True
        readme_outcome = read.outcome
        if read.outcome != "ok":
            problems.append(f"README read {read.outcome}: {read.detail}")
    llms_present = has_case_insensitive(names, "llms.txt")

    if (row.get("related_doi") or row.get("doi")) and not has_case_insensitive(names, "CITATION.cff"):
        observations.append("publication-linked repository has no root CITATION.cff")
    if not any(name.lower().startswith(("license", "licence")) for name in names):
        observations.append("no root license file observed; reuse policy not inferred")
    if not has_case_insensitive(names, "AGENTS.md"):
        observations.append("no root AGENTS.md observed; not required by this inventory")

    normalized = readme_text.lower()
    stale_readme_hit = False
    placeholder_hit = False
    structural_terms: tuple[str, ...] = ()
    if readme_outcome == "ok":
        for label, pattern in STALE_README_PATTERNS.items():
            if pattern.search(readme_text):
                stale_readme_hit = True
                problems.append(f"README contains {label}")
        for label, needle in README_PLACEHOLDERS.items():
            if needle.lower() in normalized:
                placeholder_hit = True
                problems.append(f"README contains {label}: {needle}")
        structural_terms = tuple(
            label for label, terms in README_TERMS.items() if any(term in normalized for term in terms)
        )
        observations.append(
            f"structural README terms matched {len(structural_terms)}/{len(README_TERMS)} categories; semantic review not_evaluated"
        )
        source_links = linked_source_paths(readme_text)
        if source_links:
            tree = fetch_tree(repo, snapshot)
            if tree.outcome == "ok":
                for path in sorted(source_links):
                    if path not in tree.paths and not any(
                        item.startswith(f"{path}/") for item in tree.paths
                    ):
                        problems.append(f"linked tracked source missing at snapshot: {path}")
            else:
                problems.append(f"source-link inventory {tree.outcome}: {tree.detail}")

    return Result(
        repo,
        problems,
        readme_present=readme_present,
        llms_present=llms_present,
        stale_readme_hit=stale_readme_hit,
        placeholder_hit=placeholder_hit,
        snapshot_sha=snapshot.sha,
        readme_path=readme_path,
        readme_outcome=readme_outcome,
        role=role,
        structural_terms=structural_terms,
        observations=tuple(observations),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="research-repositories.csv")
    parser.add_argument("--repos", nargs="*", help="Optional subset of repository names")
    parser.add_argument(
        "--ref",
        action="append",
        default=[],
        metavar="REPO=REF",
        help="Check a repository at a non-default branch or tag.",
    )
    parser.add_argument(
        "--advisory",
        action="store_true",
        help="Report repository-readiness gaps without failing the site build.",
    )
    parser.add_argument(
        "--report",
        help="Optional CSV report with README stale-heading and llms.txt status.",
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
        rows = [
            row
            for row in rows
            if (row.get("repository") or row.get("repo")) in wanted
            or (row.get("repository") or row.get("repo", "")).split("/", 1)[-1] in wanted
        ]

    results = [audit_repo(row, refs) for row in rows]
    failing = [result for result in results if result.problems]

    for result in results:
        if result.problems:
            print(f"FAIL {result.repo} (structural inventory; semantic review not_evaluated)")
            for problem in result.problems:
                print(f"  - {problem}")
        else:
            print(f"PASS {result.repo} (structural inventory only; semantic review not_evaluated)")
        if result.snapshot_sha:
            print(f"  snapshot: {result.snapshot_sha}")
        print(f"  README: {result.readme_path or '-'} [{result.readme_outcome}]")
        for observation in result.observations:
            print(f"  observation: {observation}")

    if args.report:
        with Path(args.report).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "repo",
                    "readme_present",
                    "llms_present",
                    "stale_readme_hit",
                    "placeholder_hit",
                    "problem_count",
                    "problems",
                    "snapshot_sha",
                    "readme_path",
                    "readme_outcome",
                    "role",
                    "semantic_review",
                    "structural_terms",
                    "observations",
                ],
            )
            writer.writeheader()
            for result in results:
                writer.writerow(
                    {
                        "repo": result.repo,
                        "readme_present": result.readme_present,
                        "llms_present": result.llms_present,
                        "stale_readme_hit": result.stale_readme_hit,
                        "placeholder_hit": result.placeholder_hit,
                        "problem_count": len(result.problems),
                        "problems": " | ".join(result.problems),
                        "snapshot_sha": result.snapshot_sha,
                        "readme_path": result.readme_path,
                        "readme_outcome": result.readme_outcome,
                        "role": result.role,
                        "semantic_review": result.semantic_review,
                        "structural_terms": " | ".join(result.structural_terms),
                        "observations": " | ".join(result.observations),
                    }
                )

    print(f"\nAudited {len(results)} repositories; {len(failing)} failing.")
    return 0 if args.advisory else (1 if failing else 0)


if __name__ == "__main__":
    sys.exit(main())
