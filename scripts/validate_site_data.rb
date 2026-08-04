#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "set"
require "yaml"

ROOT = File.expand_path("..", __dir__)
PROHIBITED_TITLES = [
  "Medical AI Lead",
  "Clinical AI Lead",
  "Clinical Research Lead",
  "Clinical Research Director"
].freeze

def load_yaml(path)
  YAML.safe_load_file(File.join(ROOT, path), aliases: false) || {}
rescue Psych::SyntaxError => e
  abort "Invalid YAML in #{path}: #{e.message}"
end

errors = []
person = load_yaml("_data/person.yml")
cv = load_yaml("_data/cv.yml")
work = load_yaml("_data/work.yml")
routes = load_yaml("config/routes.yml")

%w[name summary primary_affiliation secondary_affiliations email profiles image social_preview disclosure].each do |key|
  errors << "person.yml missing #{key}" if person[key].nil? || person[key].respond_to?(:empty?) && person[key].empty?
end

social_preview = person["social_preview"] || {}
%w[path mime_type width height alt].each do |key|
  errors << "person.yml social_preview missing #{key}" if social_preview[key].nil? || social_preview[key].respond_to?(:empty?) && social_preview[key].empty?
end
errors << "social preview must be a local PNG" unless social_preview["path"]&.match?(%r{\A/images/[^/]+\.png\z}) && social_preview["mime_type"] == "image/png"
errors << "social preview dimensions must be 1200x630" unless social_preview["width"] == 1200 && social_preview["height"] == 630

preview_path = File.join(ROOT, social_preview["path"].to_s.sub(%r{\A/}, ""))
if File.file?(preview_path)
  header = File.binread(preview_path, 24)
  if header.start_with?("\x89PNG\r\n\x1a\n".b) && header.bytesize >= 24
    width, height = header.byteslice(16, 8).unpack("NN")
    errors << "social preview file dimensions must be 1200x630" unless width == 1200 && height == 630
  else
    errors << "social preview file is not a valid PNG"
  end
else
  errors << "social preview asset is missing: #{social_preview['path']}"
end

primary = person.dig("primary_affiliation", "organization")
secondary = Array(person["secondary_affiliations"]).map { |item| item["organization"] }
errors << "primary and secondary affiliations must differ" if secondary.include?(primary)

canonical_text = [person, cv].to_json
PROHIBITED_TITLES.each do |title|
  errors << "superseded current title remains: #{title}" if canonical_text.include?(title)
end

sections = Array(work["sections"])
section_keys = sections.map { |section| section["key"] }
errors << "work section keys must be unique" unless section_keys.uniq.length == section_keys.length

items = Array(work["items"])
repositories = Array(work["repositories"])
records = items + repositories
ids = records.map { |record| record["id"] }
duplicates = ids.tally.select { |_id, count| count > 1 }.keys
errors << "duplicate work IDs: #{duplicates.join(', ')}" unless duplicates.empty?

dois = records.filter_map { |record| record["doi"]&.downcase }
duplicate_dois = dois.tally.select { |_doi, count| count > 1 }.keys
errors << "duplicate DOIs: #{duplicate_dois.join(', ')}" unless duplicate_dois.empty?

known_ids = ids.to_set
records.each do |record|
  errors << "#{record['id']} has unknown section #{record['section']}" unless section_keys.include?(record["section"])
  Array(record["related_ids"]).each do |target|
    errors << "#{record['id']} references missing #{target}" unless known_ids.include?(target)
  end
  if record["related_id"] && !known_ids.include?(record["related_id"])
    errors << "#{record['id']} references missing #{record['related_id']}"
  end
  if record["repository"] && record["repository"] !~ %r{\Areblocke/[^/]+\z}
    errors << "invalid repository name #{record['repository']}"
  end
  if record["doi"] && record["doi"] != record["doi"].downcase
    errors << "DOI must be lowercase: #{record['doi']}"
  end
  selected = record["selected"] || {}
  if selected.values.any? || record["selected_work"]
    errors << "selected record #{record['id']} requires an integer order" unless record["order"].is_a?(Integer)
  end
end

github_path = File.join(ROOT, "_data/external/github_repositories.generated.json")
if File.exist?(github_path)
  github_records = JSON.parse(File.read(github_path))
  github_records.each do |record|
    errors << "generated GitHub record is not explicitly public: #{record['full_name']}" unless record["visibility"] == "public"
    errors << "generated GitHub owner is not reblocke: #{record['full_name']}" unless record["full_name"]&.start_with?("reblocke/")
  end
end

catalog_path = File.join(ROOT, "research-repositories.json")
if File.exist?(catalog_path)
  prohibited_columns = %w[readme_gaps planned_pr pending_review remediation_status]
  JSON.parse(File.read(catalog_path)).each do |record|
    found = record.keys & prohibited_columns
    errors << "generated catalog contains maintenance-only fields: #{found.join(', ')}" unless found.empty?
  end
end

homepage = items.select { |item| item.dig("selected", "homepage") }
errors << "homepage must contain 3 to 6 selected works" unless (3..6).cover?(homepage.length)

Array(routes["canonical"]).each do |route|
  errors << "canonical route must begin and end with /: #{route}" unless route.start_with?("/") && route.end_with?("/")
end
Array(routes["redirects"]).each do |redirect|
  errors << "redirect missing from/to" unless redirect["from"] && redirect["to"]
end

if errors.empty?
  puts "Site data valid: #{records.length} work records, #{homepage.length} homepage selections."
else
  warn errors.map { |error| "ERROR: #{error}" }.join("\n")
  exit 1
end
