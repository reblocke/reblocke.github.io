#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "metadata_reconciliation"

def assert(condition, message)
  raise message unless condition
end

work = {
  "items" => [
    {
      "id" => "doi:10.1000/typography",
      "doi" => "10.1000/typography",
      "title" => "Hickam's Dictum",
      "authors" => "Locke BW, Brown J",
      "year" => 2024
    },
    {
      "id" => "doi:10.1000/conflict",
      "doi" => "10.1000/conflict",
      "title" => "Canonical title",
      "authors" => "Locke BW et al",
      "venue" => "CHEST",
      "year" => 2025
    }
  ],
  "repositories" => [
    {"id" => "repo:doi", "doi" => "10.1000/repository"},
    {"id" => "repo:pmid", "pmid" => "12345"}
  ]
}
orcid_records = [
  {"put_code" => 1, "doi" => "https://doi.org/10.1000/TYPOGRAPHY"},
  {"put_code" => 2, "doi" => "10.1000/repository"},
  {"put_code" => 3, "pmid" => "PMID: 12345"},
  {"put_code" => 4, "doi" => "10.1000/new"},
  {"put_code" => 5, "title" => "Identifier-free candidate"}
]
crossref_records = [
  {
    "doi" => "10.1000/typography",
    "title" => "Hickam’s dictum.",
    "authors" => "Locke, Brian W.; Brown, Jeanette",
    "venue" => "Journal of Diagnostic Reasoning",
    "year" => 2024
  },
  {
    "doi" => "10.1000/conflict",
    "title" => "Different title",
    "authors" => "Locke, Brian W.; Brown, Jeanette; Smith, Priya",
    "venue" => "Different Journal",
    "year" => 2026
  }
]

result = MetadataReconciliation.build(work: work, orcid_records: orcid_records, crossref_records: crossref_records)
assert(result["orcid_candidates"].map { |record| record["put_code"] } == [4, 5], "represented ORCID records were not suppressed")
assert(result["missing_canonical_fields"].length == 1, "missing canonical field was not isolated")
assert(result["missing_canonical_fields"][0]["fields"].map { |field| field["field"] } == ["venue"], "wrong missing field")
assert(result["source_conflicts"].length == 1, "typographic or author-format noise became a conflict")
assert(result["source_conflicts"][0]["fields"].map { |field| field["field"] } == %w[title venue year], "true conflicts were not preserved")
assert(MetadataReconciliation.equivalent?("venue", "Conference / Journal Series", "Journal Series"), "curated venue enrichment became a conflict")
assert(!MetadataReconciliation.equivalent?("venue", "Journal of Lung Research", "Lung"), "venue substring hid a conflict")
assert(MetadataReconciliation.equivalent?("title", "Anti-obesity methods", "Anti‐obesity methods."), "typographic title variation became a conflict")
assert(
  MetadataReconciliation.equivalent?("title", "Letter: Author Response", "<i>Letter:</i>\n Author Response."),
  "Crossref title markup became a conflict"
)
assert(!MetadataReconciliation.equivalent?("title", "C++ methods", "C methods"), "meaningful scholarly punctuation was erased")
assert(!MetadataReconciliation.authors_equivalent?("Locke BW et al", "Smith, Priya; Locke, Brian W."), "changed first author was hidden")
assert(!MetadataReconciliation.authors_equivalent?("Locke BW, Brown J", "Locke, Brian W.; Smith, Priya"), "changed complete author sequence was hidden")

json = MetadataReconciliation.stable_pretty_json({"items" => [], "metadata" => {}})
assert(json.include?('"items": []'), "empty arrays are not serialized compactly")
assert(json.include?('"metadata": {}'), "empty objects are not serialized compactly")

puts "Metadata reconciliation tests passed."
