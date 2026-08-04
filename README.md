# Brian W. Locke academic website

This repository publishes <https://reblocke.github.io/> as a small static Jekyll site and maintains its public scholarly metadata.

## Routine edits

Human-maintained facts live in only three files:

- `_data/person.yml`: identity, affiliations, profiles, portrait, and disclosure.
- `_data/cv.yml`: appointments, training, support, teaching, service, and honors.
- `_data/work.yml`: curated publications, presentations, repositories, relationships, and editorial selections.

Files under `_data/external/`, `_data/generated/`, `llms.txt`, and `research-repositories.*` are generated. Do not edit them manually.

## Local development

Install Ruby 3.3.12 and Bundler, then run:

```bash
bundle install
bin/check
bundle exec jekyll serve
```

The local site is available at <http://127.0.0.1:4000/>.

To regenerate deterministic outputs after editing canonical data:

```bash
bundle exec ruby scripts/generate_indexes.rb --write
bin/check
```

## External metadata refresh

The monthly workflow retrieves public metadata from GitHub, ORCID, Crossref, and PubMed, regenerates the site, validates it, and opens a review pull request. It never publishes directly.

The generated reconciliation report separates unmatched ORCID candidates, fields missing from canonical records, and material source conflicts. DOI or PMID matches anywhere in the canonical work registry count as represented; external metadata never overwrites curated content automatically.

The refresh retains the website repository's public GitHub metadata but omits its self-changing `updated_at` value so deployment commits do not manufacture metadata-only pull requests.

Run the refresh locally with:

```bash
GITHUB_TOKEN="$(gh auth token)" bundle exec ruby scripts/refresh_external_metadata.rb
bundle exec ruby scripts/generate_indexes.rb --write
bin/check
```

`ORCID_CLIENT_ID` and `ORCID_CLIENT_SECRET` may be configured for authenticated ORCID Public API access. The public endpoint is used for this single public record when credentials are absent. `NCBI_API_KEY` is optional for higher PubMed request limits.

Google Scholar remains the linked comprehensive profile. It does not provide a supported automated profile API, so the site does not scrape it.

## Publishing

Pull requests and `master` run the same `bin/check` build. A push to `master` deploys the exact validated `_site` artifact through GitHub Pages Actions. Repository Settings → Pages → Build and deployment must use **GitHub Actions**.

## Public-content boundary

Do not commit PHI, restricted datasets, credentials, private repository names, collaborator-only drafts, unpublished grant material, or publisher-formatted PDFs. Link to DOI, PubMed, PubMed Central, accepted manuscripts with verified rights, and public repositories.

## License and attribution

See [LICENSE](./LICENSE) and [NOTICE.md](./NOTICE.md).
