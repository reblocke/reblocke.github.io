# Brian W. Locke academic website

This repository publishes the personal academic website at <https://reblocke.github.io/> and the public machine-readable index for research repositories.

## Links

- Website: <https://reblocke.github.io/>
- LLM index: <https://reblocke.github.io/llms.txt>
- Research repository page: <https://reblocke.github.io/research-repositories/>
- Public audit manifest: [`research_repository_audit.csv`](./research_repository_audit.csv)

## Purpose

The site collects publications, teaching materials, clinical research resources, and links to reproducible code repositories. The root `llms.txt` and audit manifest are designed to help language-model agents find the correct repository, DOI, citation metadata, and data-access limitations without guessing from paywalled PDFs or incomplete GitHub descriptions.

## Repository Layout

| Path | Purpose |
|---|---|
| `_pages/` | Website pages, including the research repository index. |
| `_publications/` | Publication entries rendered by the academicpages theme. |
| `_talks/` and `_portfolio/` | Teaching, talk, and project pages. |
| `files/` | Public downloadable files used by the website. |
| `llms.txt` | Public machine-readable research index. |
| `research_repository_audit.csv` | Public audit manifest for research and teaching repositories. |
| `scripts/audit_llm_readiness.py` | CLI audit for READMEBuilder and LLM-readiness surfaces. |

## Local Development

Install Ruby dependencies if needed, then run the Jekyll site locally:

```bash
bundle install
bundle exec jekyll serve
```

The site should be available at `http://localhost:4000`.

## LLM-Readiness Audit

Run the public repository audit with:

```bash
python3 scripts/audit_llm_readiness.py --manifest research_repository_audit.csv
```

To check only a subset while preparing a small PR batch:

```bash
python3 scripts/audit_llm_readiness.py --manifest research_repository_audit.csv --repos NRH-SCI-Vent AOM-and-Bari-Surg-for-OSA-SRMA notebooks_dx_reasoning
```

The audit intentionally exits nonzero when a repository is missing root `README.md`, `CITATION.cff` for publication-linked work, a license file, `AGENTS.md`, or core READMEBuilder content categories.

## Data, Manuscripts, and Copyright

This public website must not include PHI, restricted datasets, private grant drafts, collaborator-only manuscripts, credentials, or publisher-formatted article text. Manuscript Markdown should be added only after confirming that an author-owned accepted manuscript, preprint, or other reusable version is available.

## License

The underlying academicpages/minimal-mistakes theme code remains under its original MIT-compatible licensing. Original site text and repository-audit metadata are copyright Brian W. Locke unless otherwise noted.

## Contact

Maintainer: Brian W. Locke (`@reblocke`)
