# frozen_string_literal: true

require "cgi"
require "json"
require "set"

module MetadataReconciliation
  module_function

  def stable_pretty_json(value)
    JSON.pretty_generate(value).gsub(/\[\s*\]/m, "[]").gsub(/\{\s*\}/m, "{}")
  end

  def normalize_doi(value)
    value.to_s.strip.sub(%r{\Ahttps?://(?:dx\.)?doi\.org/}i, "").sub(/\Adoi:\s*/i, "").downcase
  end

  def normalize_pmid(value)
    value.to_s.strip.sub(/\Apmid:\s*/i, "")
  end

  def normalize_text(value)
    CGI.unescapeHTML(value.to_s.gsub(/<[^>]+>/, ""))
      .unicode_normalize(:nfkc)
      .gsub(/[‘’]/, "'")
      .gsub(/[‐‑‒–—―−]/, "-")
      .downcase
      .strip
      .sub(/[.]\z/, "")
      .split
      .join(" ")
  end

  def normalize_name(value)
    normalize_text(value).gsub(/[\p{P}\p{S}]+/, " ").split.join(" ")
  end

  def source_author_families(value)
    value.to_s.split(/\s*;\s*/).filter_map do |author|
      family = author.split(",", 2).first
      normalized = normalize_name(family)
      normalized unless normalized.empty?
    end
  end

  def canonical_author_families(value)
    value.to_s.split(/\s*,\s*/).filter_map do |author|
      family = author.sub(/\s+et\s+al\.?\z/i, "").sub(/\s+(?:[A-Z][A-Z.\-]*\s*)+\z/, "")
      normalized = normalize_name(family)
      normalized unless normalized.empty?
    end
  end

  def authors_equivalent?(canonical, source)
    canonical_families = canonical_author_families(canonical)
    source_families = source_author_families(source)
    return false if canonical_families.empty? || source_families.empty?

    if canonical.to_s.match?(/\bet\s+al\.?\z/i)
      source_families.first(canonical_families.length) == canonical_families
    else
      source_families == canonical_families
    end
  end

  def equivalent?(field, canonical, source)
    case field
    when "authors"
      authors_equivalent?(canonical, source)
    when "year"
      canonical.to_i == source.to_i
    when "venue"
      canonical_text = normalize_text(canonical)
      source_text = normalize_text(source)
      canonical_text == source_text || canonical.to_s.split(/\s+\/\s+/).map { |part| normalize_text(part) }.include?(source_text)
    else
      normalize_text(canonical) == normalize_text(source)
    end
  end

  def build(work:, orcid_records:, crossref_records:)
    items = Array(work["items"])
    canonical_records = items + Array(work["repositories"])
    canonical_dois = canonical_records.filter_map do |record|
      doi = normalize_doi(record["doi"])
      doi unless doi.empty?
    end.to_set
    canonical_pmids = canonical_records.filter_map do |record|
      pmid = normalize_pmid(record["pmid"])
      pmid unless pmid.empty?
    end.to_set

    candidates = Array(orcid_records).reject do |record|
      doi = normalize_doi(record["doi"])
      pmid = normalize_pmid(record["pmid"])
      (!doi.empty? && canonical_dois.include?(doi)) || (!pmid.empty? && canonical_pmids.include?(pmid))
    end

    items_by_doi = items.to_h { |item| [normalize_doi(item["doi"]), item] }
    missing_fields = []
    source_conflicts = []
    Array(crossref_records).each do |record|
      canonical = items_by_doi[normalize_doi(record["doi"])]
      next unless canonical

      missing = []
      conflicts = []
      %w[title authors venue year].each do |field|
        source = record[field]
        next if source.nil? || source == ""

        if canonical[field].nil? || canonical[field] == ""
          missing << {"field" => field, "source" => source}
        elsif !equivalent?(field, canonical[field], source)
          conflicts << {"field" => field, "canonical" => canonical[field], "source" => source}
        end
      end

      base = {"id" => canonical["id"], "doi" => normalize_doi(record["doi"]), "source" => "Crossref"}
      missing_fields << base.merge("fields" => missing) unless missing.empty?
      source_conflicts << base.merge("fields" => conflicts) unless conflicts.empty?
    end

    {
      "orcid_candidates" => candidates,
      "missing_canonical_fields" => missing_fields,
      "source_conflicts" => source_conflicts
    }
  end
end
