# AGENTS

## Purpose and public boundary

This public repository publishes Brian W. Locke's academic website and public scholarly metadata. Never add PHI, restricted data, credentials, private repository names, collaborator-only drafts, financial files, unpublished grants, or publisher-formatted PDFs.

## Canonical sources

- Human-maintained data: `_data/person.yml`, `_data/cv.yml`, and `_data/work.yml`.
- Generated data: `_data/external/`, `_data/generated/`, `llms.txt`, and `research-repositories.*`.
- Identity, affiliations, disclosure, selection, summaries, relationships, and editorial order must not be inferred from external metadata.
- New ORCID works remain reconciliation candidates until reviewed.
- Intermountain Health and MTN must remain distinct affiliations.
- Superseded current titles are prohibited.

## Required workflow

After canonical edits:

```bash
ruby scripts/generate_indexes.rb --write
bin/check
```

Do not hand-edit generated files. The normal Jekyll build must not access the network. External metadata refreshes must open review pull requests and must not deploy directly.

## Visual invariants

- Principal navigation is exactly About, Work, and CV.
- Essential content works without JavaScript.
- Use the editorial token system; do not add remote fonts, frameworks, gradients, dashboards, or ornamental motion.
- Cards are reserved for homepage featured work.
- Preserve keyboard focus, one H1 per principal page, readable mobile reflow, and CV print behavior.

## Repository readiness

The stable public repository catalog is `research-repositories.csv`. Run the readiness audit in advisory mode for the complete catalog or without it for targeted remediation:

```bash
python3 scripts/audit_llm_readiness.py --manifest research-repositories.csv --advisory
python3 scripts/audit_llm_readiness.py --manifest research-repositories.csv --repos reblocke/example
```

This audit accesses GitHub and is intentionally separate from the deterministic `bin/check` merge gate.
