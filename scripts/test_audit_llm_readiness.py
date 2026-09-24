"""Deterministic structural-inventory and fetch-boundary regressions."""

from __future__ import annotations

import base64
import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import audit_llm_readiness as audit

SHA = "a" * 40
TREE = "b" * 40
ROW = {"repository": "reblocke/example", "artifact_type": "research code"}


def fake_api(names, readme="Purpose and data.", tree_paths=(), read_error=None):
    calls = []

    def run(args):
        endpoint = args[1]
        calls.append(endpoint)
        if endpoint == "repos/reblocke/example":
            return json.dumps({"default_branch": "main"})
        if endpoint == "repos/reblocke/example/commits/main":
            return json.dumps({"sha": SHA, "commit": {"tree": {"sha": TREE}}})
        if endpoint == f"repos/reblocke/example/contents?ref={SHA}":
            return json.dumps([{"name": name} for name in names])
        if endpoint.startswith("repos/reblocke/example/contents/"):
            if read_error:
                raise audit.GhError(read_error)
            content = base64.b64encode(readme.encode("utf-8") if isinstance(readme, str) else readme)
            return json.dumps({"encoding": "base64", "content": content.decode()})
        if endpoint == f"repos/reblocke/example/git/trees/{TREE}?recursive=1":
            return json.dumps({"truncated": False, "tree": [{"path": p} for p in tree_paths]})
        raise AssertionError(f"unexpected endpoint: {endpoint}")

    return run, calls


class AuditorTests(unittest.TestCase):
    def test_keyword_complete_and_negated_prose_is_only_structural(self):
        prose = " ".join(terms[0] for terms in audit.README_TERMS.values())
        run, _ = fake_api(["README.md"], f"Nothing is ready. Not reproducible. {prose}")
        with patch.object(audit, "run_gh", run):
            result = audit.audit_repo(ROW, {})
        self.assertEqual(result.structural_terms, tuple(audit.README_TERMS))
        self.assertEqual(result.semantic_review, "not_evaluated")
        self.assertFalse(result.problems)

    def test_case_sensitive_readme_path_and_immutable_snapshot(self):
        run, calls = fake_api(["ReadMe.MD"], "Purpose. [source](scripts/run.py)", ["scripts/run.py"])
        with patch.object(audit, "run_gh", run):
            result = audit.audit_repo(ROW, {})
        self.assertEqual(result.readme_path, "ReadMe.MD")
        self.assertEqual(result.snapshot_sha, SHA)
        self.assertIn(f"contents/ReadMe.MD?ref={SHA}", calls[-2])
        self.assertEqual(result.readme_outcome, "ok")
        self.assertFalse(result.problems)

    def test_ambiguous_and_missing_readme_are_distinct(self):
        for names, expected in [(["README.md", "readme.md"], "ambiguous"), ([], "missing")]:
            run, calls = fake_api(names)
            with patch.object(audit, "run_gh", run):
                result = audit.audit_repo(ROW, {})
            self.assertEqual(result.readme_outcome, expected)
            self.assertTrue(result.problems)
            self.assertFalse(any("contents/README" in call for call in calls))

    def test_read_failures_do_not_become_missing_or_empty_prose(self):
        cases = [
            ("gh: Forbidden (HTTP 403)", "denied"),
            ("gh: Not Found (HTTP 404)", "unavailable"),
            ("connection reset", "failed"),
        ]
        for error, outcome in cases:
            run, _ = fake_api(["README.md"], read_error=error)
            with patch.object(audit, "run_gh", run):
                result = audit.audit_repo(ROW, {})
            self.assertTrue(result.readme_present)
            self.assertEqual(result.readme_outcome, outcome)
            self.assertTrue(any(f"README read {outcome}" in p for p in result.problems))
            self.assertFalse(any("missing READMEBuilder element" in p for p in result.problems))

    def test_non_utf8_and_unsupported_encoding(self):
        run, _ = fake_api(["README.md"], b"\xff")
        with patch.object(audit, "run_gh", run):
            result = audit.audit_repo(ROW, {})
        self.assertEqual(result.readme_outcome, "unsupported")
        self.assertTrue(result.problems)

        def unsupported(args):
            endpoint = args[1]
            if "/contents/README.md?" in endpoint:
                return json.dumps({"encoding": "none", "content": ""})
            return run(args)

        with patch.object(audit, "run_gh", unsupported):
            result = audit.audit_repo(ROW, {})
        self.assertEqual(result.readme_outcome, "unsupported")

    def test_denied_repository_tree_stays_denied(self):
        run, _ = fake_api(["README.md"])

        def denied(args):
            if "/contents?ref=" in args[1]:
                raise audit.GhError("gh: Forbidden (HTTP 403)")
            return run(args)

        with patch.object(audit, "run_gh", denied):
            result = audit.audit_repo(ROW, {})
        self.assertEqual(result.readme_outcome, "denied")
        self.assertTrue(result.problems)

    def test_missing_tracked_source_not_confused_with_external_or_generated_input(self):
        prose = (
            "[missing source](scripts/missing.py) "
            "[external input](data/external/input.csv) "
            "[generated report](reports/output.csv)"
        )
        run, _ = fake_api(["README.md"], prose, ["scripts/existing.py"])
        with patch.object(audit, "run_gh", run):
            result = audit.audit_repo(ROW, {})
        self.assertEqual(result.problems, ["linked tracked source missing at snapshot: scripts/missing.py"])

    def test_unknown_role_does_not_invent_license_or_agent_obligations(self):
        run, _ = fake_api(["README.md"], "Purpose.")
        with patch.object(audit, "run_gh", run):
            result = audit.audit_repo({**ROW, "artifact_type": "unmapped archive"}, {})
        self.assertEqual(result.role, "unknown")
        self.assertFalse(result.problems)
        self.assertTrue(any("not required" in note for note in result.observations))

    def test_report_retains_existing_columns_and_adds_evidence_status(self):
        result = audit.Result("example", [], readme_present=True, snapshot_sha=SHA, readme_outcome="ok")
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.csv"
            with patch.object(audit, "read_manifest", return_value=[ROW]), patch.object(
                audit, "audit_repo", return_value=result
            ), patch("sys.argv", ["audit", "--report", str(report)]):
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(audit.main(), 0)
            with report.open() as handle:
                reader = csv.DictReader(handle)
                old = ["repo", "readme_present", "llms_present", "stale_readme_hit", "placeholder_hit", "problem_count", "problems"]
                self.assertEqual(reader.fieldnames[: len(old)], old)
                row = next(reader)
                self.assertEqual(row["semantic_review"], "not_evaluated")
                self.assertEqual(row["snapshot_sha"], SHA)


if __name__ == "__main__":
    unittest.main()
