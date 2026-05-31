# AGENTS

## Purpose
This repository publishes Brian W. Locke's academic website and the public index for research code, teaching materials, and manuscript-adjacent repositories.

## Public-content rules
- Treat this repository as public. Do not add private repository names, collaborator-only drafts, PHI, restricted datasets, credentials, financial files, or unpublished grant material.
- Link to publisher pages, PubMed, PubMed Central, and public GitHub repositories rather than copying publisher PDFs or copyrighted article text.
- Add manuscript Markdown only when the source is an author-owned accepted manuscript, preprint, or other version with reuse rights that have been checked.

## LLM-readiness conventions
- Keep `llms.txt` concise, factual, and linked to stable public pages.
- Keep `research_repository_audit.csv` machine-readable and limited to public repositories.
- Use `scripts/audit_llm_readiness.py` before claiming that a public repository is complete.
- Each listed research repository should have a root `README.md`, clear license status, `CITATION.cff` when publication-linked, and `AGENTS.md` with repository-specific run instructions and data-access cautions.

## Local checks
- For content edits: run `git diff --check`.
- For audit edits: run `python3 scripts/audit_llm_readiness.py --manifest research_repository_audit.csv --repos <repo>`.
- For site edits: run the local Jekyll build if Ruby dependencies are available; otherwise inspect Markdown and links directly.
