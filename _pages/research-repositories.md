---
layout: archive
title: "Research Repositories"
permalink: /research-repositories/
author_profile: true
---

This page is the public entry point for research code, teaching materials, and manuscript-adjacent repositories that are intended to be findable by people and language-model agents.

Machine-readable index: [`/llms.txt`](/llms.txt)  
Audit manifest: [`/research_repository_audit.csv`](/research_repository_audit.csv)

## Repository Standards

Each publication-linked repository should include:

- a root `README.md` with title, description, instructions, authors/funding, file inventory, data/codebook notes, script order, dependency/runtime notes, citation, license, and contact information;
- `CITATION.cff` with the real DOI/PMID when the repository supports a publication;
- `AGENTS.md` with concise instructions for AI agents and human reproducibility assistants;
- clear license and data-access notes, including explicit exclusions for restricted clinical data, PHI, third-party material, and publisher-formatted article text.

## Copyright Policy

Repositories should link to publisher pages, PubMed, PubMed Central, and DOI records. Manuscript Markdown should be added only when the source is an author-owned accepted manuscript, preprint, or other version whose reuse rights have been checked.

## Current Audit

The canonical audit is maintained as CSV so it can be read by scripts and language models:

- [Public research repository audit CSV](/research_repository_audit.csv)
- [LLM index](/llms.txt)

The audit separates publication-linked repositories from teaching, simulation, and tool repositories. Private CV-linked candidates are tracked outside this public website so collaborator-only drafts and internal project names are not exposed here.
