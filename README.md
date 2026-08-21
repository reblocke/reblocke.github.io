# Brian W. Locke academic website

This repository publishes <https://reblocke.github.io/> as a small static Jekyll site and maintains its public scholarly metadata.

## Routine edits

Human-maintained facts live in only three files:

- `_data/person.yml`: identity, affiliations, profiles, portrait, and disclosure.
- `_data/cv.yml`: appointments, training, support, teaching, service, and honors.
- `_data/work.yml`: curated publications, presentations, topic collections, repositories, live project-site links, relationships, and editorial selections.

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

`bin/check` is deterministic and uses only repository-local inputs. It validates source data, regenerability, the built site, canonical indexability, structured-data graphs, rendered publication/topic completeness, and negative mutations that must be rejected. The built-site validator and mutation suite also accept an alternate artifact through `--site PATH`.

The separate **Repository readiness audit** workflow performs the networked public-repository checks monthly and on demand. To run that advisory audit locally with GitHub authentication:

```bash
GH_TOKEN="$(gh auth token)" python3 scripts/audit_llm_readiness.py --manifest research-repositories.csv --advisory
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

## Search discovery and Search Console

The generated `sitemap.xml` contains only the seven canonical routes: `/`, `/bio/`, `/work/`, `/publications/`, `/topics/hypercapnic-respiratory-failure/`, `/cv/`, and `/research-repositories/`. The generated `robots.txt` allows crawling and advertises `https://reblocke.github.io/sitemap.xml`. Canonical and historical redirect pages must not carry blocking `robots`, `googlebot`, or `bingbot` directives. The 404 and Notice pages are intentionally excluded with `noindex,follow` and omitted from the sitemap.

Each canonical page has a unique search title and description, a self-canonical URL, at least one crawlable internal link, and one schema.org `@graph` grounded in the canonical person data. `bin/check` verifies those contracts as well as rendered coverage of all non-abstract publications and the curated respiratory topic. These controls support ordinary crawler discovery without a Google account, but they do not provide Search Console reports or prove that Google has indexed a URL.

The URL-prefix property `https://reblocke.github.io/` uses a public HTML verification tag sourced from `google_site_verification` in `_config.yml` and rendered only in the homepage `<head>`. Retain the tag after verification because Google checks it periodically. If Google issues a replacement, update it through the normal pull-request and validated Pages deployment workflow.

A signed-in maintainer completes the Google-side handoff from [Google Search Console](https://search.google.com/search-console):

1. Confirm that the live homepage contains the exact verification tag, then select **Verify** for the URL-prefix property.
2. In **Sitemaps**, submit `sitemap.xml`.
3. Use **URL inspection** for the seven canonical routes listed above and request indexing when useful.

The HTML verification tag is intentionally public. Google passwords, OAuth authorization codes, access or refresh tokens, recovery codes, and browser-session data are secrets and must never be committed or shared for this workflow. Sitemap submission and indexing requests are asynchronous and do not guarantee immediate indexing.

## Public-content boundary

Do not commit PHI, restricted datasets, credentials, private repository names, collaborator-only drafts, unpublished grant material, or publisher-formatted PDFs. Link to DOI, PubMed, PubMed Central, accepted manuscripts with verified rights, and public repositories.

Project-site links are an editorial allowlist, not an automatic mirror of every GitHub Pages deployment. Add paired `live_url` and `live_label` fields only for a selected public repository whose site is stable, useful to visitors, and safe to surface. The generator carries those fields into JSON and CSV, and the rendered Work and repository-catalog pages must both link to each curated site. Individual project repositories retain ownership of their own crawling, metadata, accessibility, and release policy.

## License and attribution

See [LICENSE](./LICENSE) and [NOTICE.md](./NOTICE.md).
