#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "json"
require "set"
require "uri"
require "yaml"

ROOT = File.expand_path("..", __dir__)
PROHIBITED_TITLES = [
  "Medical AI Lead",
  "Clinical AI Lead",
  "Clinical Research Lead",
  "Clinical Research Director"
].freeze
EXPECTED_CANONICAL_ROUTES = [
  "/",
  "/bio/",
  "/work/",
  "/publications/",
  "/topics/hypercapnic-respiratory-failure/",
  "/cv/",
  "/research-repositories/"
].freeze
EXPECTED_TOPIC = {
  "id" => "hypercapnic-respiratory-failure",
  "title" => "Hypercapnic Respiratory Failure and Respiratory Measurement",
  "permalink" => "/topics/hypercapnic-respiratory-failure/"
}.freeze
EXPECTED_TOPIC_ITEM_IDS = [
  "doi:10.1016/j.chest.2025.08.002",
  "doi:10.64898/2026.07.03.26357242",
  "doi:10.1111/obr.13697",
  "doi:10.1177/19433654261424871",
  "doi:10.1016/j.jsmc.2024.02.012",
  "doi:10.3390/ijerph19095473",
  "doi:10.4187/respcare.11573",
  "doi:10.1093/ajrccm/aamag162.4637",
  "doi:10.1093/ajrccm/aamag162.4737",
  "abstract:chest:2025:tcco2-sensor-performance",
  "abstract:ats:2025:tcco2-performance",
  "abstract:chest:2024:hypercapnia-adverse-events",
  "abstract:ats:2024:bicarbonate-hypercapnia"
].freeze
EXPECTED_CATALOG_COLUMNS = %w[
  repository title artifact_type analysis_language related_doi related_pmid
  data_availability license_status public_url live_url live_label archived
  default_branch latest_release
].freeze

def load_yaml(path)
  YAML.safe_load_file(File.join(ROOT, path), aliases: false) || {}
rescue Psych::SyntaxError => e
  abort "Invalid YAML in #{path}: #{e.message}"
end

def nonempty_string?(value)
  value.is_a?(String) && !value.strip.empty?
end

def valid_https_url?(value)
  return false unless nonempty_string?(value)

  uri = URI.parse(value)
  uri.is_a?(URI::HTTPS) && nonempty_string?(uri.host)
rescue URI::InvalidURIError
  false
end

errors = []
config = load_yaml("_config.yml")
person = load_yaml("_data/person.yml")
cv = load_yaml("_data/cv.yml")
work = load_yaml("_data/work.yml")
routes = load_yaml("config/routes.yml")
navigation = load_yaml("_data/navigation.yml")

verification_token = config["google_site_verification"].to_s
errors << "_config.yml missing google_site_verification" if verification_token.empty?
unless verification_token.empty? || verification_token.match?(%r{\A[A-Za-z0-9_-]+\z})
  errors << "_config.yml google_site_verification has an invalid format"
end

%w[name summary research_statement clinical_role email profiles image social_preview disclosure].each do |key|
  errors << "person.yml missing #{key}" if person[key].nil? || person[key].respond_to?(:empty?) && person[key].empty?
end

biography = Array(person["biography"])
errors << "person.yml biography must contain exactly three paragraphs" unless biography.length == 3
biography.each_with_index do |paragraph, index|
  errors << "person.yml biography paragraph #{index + 1} must be nonempty text" unless paragraph.is_a?(String) && !paragraph.strip.empty?
end

research_themes = Array(person["research_themes"])
errors << "person.yml research_themes must contain exactly three themes" unless research_themes.length == 3
research_themes.each_with_index do |theme, index|
  unless theme.is_a?(Hash)
    errors << "person.yml research theme #{index + 1} must be an object"
    next
  end
  %w[title description].each do |key|
    value = theme[key]
    errors << "person.yml research theme #{index + 1} missing #{key}" unless value.is_a?(String) && !value.strip.empty?
  end
end

primary_affiliation = person["primary_affiliation"]
unless primary_affiliation.is_a?(Hash)
  errors << "person.yml primary_affiliation must be an object"
  primary_affiliation = {}
end
%w[role organization].each do |key|
  errors << "person.yml primary_affiliation missing #{key}" unless nonempty_string?(primary_affiliation[key])
end

clinical_context = person["clinical_context"]
unless clinical_context.is_a?(Array) && !clinical_context.empty?
  errors << "person.yml clinical_context must be a nonempty list"
  clinical_context = []
end
clinical_context.each_with_index do |context, index|
  errors << "person.yml clinical_context item #{index + 1} must be nonempty text" unless nonempty_string?(context)
end

secondary_affiliations = person["secondary_affiliations"]
unless secondary_affiliations.is_a?(Array) && !secondary_affiliations.empty?
  errors << "person.yml secondary_affiliations must be a nonempty list"
  secondary_affiliations = []
end
secondary_affiliations.each_with_index do |affiliation, index|
  unless affiliation.is_a?(Hash)
    errors << "person.yml secondary affiliation #{index + 1} must be an object"
    next
  end
  %w[role organization legal_name descriptor].each do |key|
    unless nonempty_string?(affiliation[key])
      errors << "person.yml secondary affiliation #{index + 1} missing #{key}"
    end
  end
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

primary = primary_affiliation["organization"]
secondary = secondary_affiliations.filter_map do |item|
  item["organization"] if item.is_a?(Hash) && nonempty_string?(item["organization"])
end
errors << "primary and secondary affiliations must differ" if secondary.include?(primary)

current_positions = Array(cv["positions"]).select { |position| position["status"] == "current" }
primary_role = primary_affiliation["role"]
primary_match = current_positions.any? do |position|
  position["title"] == primary_role && position["organization"] == primary
end
unless primary_match
  errors << "person.yml primary affiliation does not match a current cv.yml position: #{primary_role}, #{primary}"
end

clinical_role = person["clinical_role"]
clinical_match = current_positions.any? do |position|
  organization = position["organization"].to_s
  !clinical_context.empty? &&
    position["title"] == clinical_role &&
    organization.include?(primary.to_s) &&
    clinical_context.all? { |context| organization.include?(context.to_s) }
end
unless clinical_match
  errors << "person.yml clinical role and context do not match a current cv.yml position: #{clinical_role}"
end

secondary_affiliations.each do |affiliation|
  next unless affiliation.is_a?(Hash)

  names = [affiliation["organization"], affiliation["legal_name"]].select { |name| nonempty_string?(name) }
  match = current_positions.any? do |position|
    organization = position["organization"].to_s
    !names.empty? &&
      position["title"] == affiliation["role"] &&
      names.all? { |name| organization.include?(name) }
  end
  unless match
    errors << "person.yml secondary affiliation does not match a current cv.yml position: #{affiliation['role']}, #{affiliation['organization']}"
  end
end

schema = person["schema"]
unless schema.is_a?(Hash)
  errors << "person.yml schema must be an object"
  schema = {}
end

expected_schema_ids = {
  "person_id" => "https://reblocke.github.io/#person",
  "website_id" => "https://reblocke.github.io/#website",
  "portrait_id" => "https://reblocke.github.io/#portrait"
}
expected_schema_ids.each do |key, expected|
  errors << "person.yml schema #{key} must be #{expected}" unless schema[key] == expected
end
errors << "person.yml schema type must be Person" unless schema["type"] == "Person"
errors << "person.yml schema display_name must be nonempty" unless nonempty_string?(schema["display_name"])

{
  "alternate_names" => schema["alternate_names"],
  "honorific_suffixes" => schema["honorific_suffixes"],
  "job_titles" => schema["job_titles"],
  "knows_about" => schema["knows_about"]
}.each do |key, values|
  unless values.is_a?(Array) && !values.empty? && values.all? { |value| nonempty_string?(value) } && values.uniq == values
    errors << "person.yml schema #{key} must be a nonempty list of unique strings"
  end
end
unless Array(schema["honorific_suffixes"]) == Array(person["credentials"])
  errors << "person.yml schema honorific_suffixes must match credentials"
end
unless Array(schema["job_titles"]).include?(primary_affiliation["role"]) && Array(schema["job_titles"]).include?(person["clinical_role"])
  errors << "person.yml schema job_titles must include the primary and clinical roles"
end

orcid_id = schema["orcid_id"]
unless nonempty_string?(orcid_id) && orcid_id.match?(%r{\A\d{4}-\d{4}-\d{4}-\d{3}[\dX]\z})
  errors << "person.yml schema orcid_id has an invalid format"
end
unless person.dig("profiles", "orcid") == "https://orcid.org/#{orcid_id}"
  errors << "person.yml schema orcid_id must match profiles.orcid"
end

organizations = schema["organizations"]
unless organizations.is_a?(Hash) && organizations.keys.sort == %w[advisor employer university]
  errors << "person.yml schema organizations must contain exactly employer, university, and advisor"
  organizations = {}
end
organization_ids = []
{
  "employer" => "Organization",
  "university" => "CollegeOrUniversity",
  "advisor" => "Organization"
}.each do |key, expected_type|
  organization = organizations[key]
  unless organization.is_a?(Hash)
    errors << "person.yml schema organization #{key} must be an object"
    next
  end
  %w[id name].each do |field|
    errors << "person.yml schema organization #{key} missing #{field}" unless nonempty_string?(organization[field])
  end
  organization_ids << organization["id"] if nonempty_string?(organization["id"])
  unless organization["id"].to_s.match?(%r{\Ahttps://reblocke\.github\.io/#[a-z0-9-]+\z})
    errors << "person.yml schema organization #{key} needs a stable site-fragment id"
  end
  errors << "person.yml schema organization #{key} type must be #{expected_type}" unless organization["type"] == expected_type
  if %w[employer university].include?(key) && !valid_https_url?(organization["url"])
    errors << "person.yml schema organization #{key} needs an HTTPS url"
  end
  if key == "advisor" && !nonempty_string?(organization["alternate_name"])
    errors << "person.yml schema organization advisor needs alternate_name"
  end
end
errors << "person.yml schema organization ids must be unique" unless organization_ids.uniq == organization_ids

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
  live_url = record["live_url"]
  live_label = record["live_label"]
  if !!live_url != !!live_label || (live_url && (!nonempty_string?(live_url) || !nonempty_string?(live_label)))
    errors << "#{record['id']} live_url and live_label must be present together as nonempty strings"
  elsif live_url
    errors << "#{record['id']} live_url must be HTTPS" unless valid_https_url?(live_url)
    errors << "#{record['id']} live metadata is allowed only for repositories" unless record["repository"]
    errors << "#{record['id']} live metadata requires selected_work" unless record["selected_work"]
    expected_live_url = "https://reblocke.github.io/#{record['repository'].to_s.split('/', 2).last}/"
    errors << "#{record['id']} live_url must be its GitHub Pages project root #{expected_live_url}" unless live_url == expected_live_url
  end
  selected = record["selected"] || {}
  if selected.values.any? || record["selected_work"]
    errors << "selected record #{record['id']} requires an integer order" unless record["order"].is_a?(Integer)
  end
end

items.reject { |item| item["type"] == "abstract" }.each do |item|
  %w[title authors venue].each do |field|
    errors << "#{item['id']} non-abstract publication missing #{field}" unless nonempty_string?(item[field])
  end
  errors << "#{item['id']} non-abstract publication missing year" unless item["year"].is_a?(Integer)
end

topics = Array(work["topics"])
unless topics.length == 1
  errors << "work topics must contain exactly one curated topic"
end
topic_ids = topics.filter_map { |topic| topic["id"] if topic.is_a?(Hash) }
errors << "work topic ids must be unique" unless topic_ids.uniq == topic_ids
item_ids = items.map { |item| item["id"] }.to_set
topics.each_with_index do |topic, index|
  unless topic.is_a?(Hash)
    errors << "work topic #{index + 1} must be an object"
    next
  end
  expected_keys = %w[description id item_ids permalink title]
  errors << "work topic #{index + 1} must contain exactly #{expected_keys.join(', ')}" unless topic.keys.sort == expected_keys
  EXPECTED_TOPIC.each do |key, expected|
    errors << "work topic #{index + 1} #{key} must be #{expected.inspect}" unless topic[key] == expected
  end
  errors << "work topic #{index + 1} description must be nonempty" unless nonempty_string?(topic["description"])
  members = topic["item_ids"]
  unless members.is_a?(Array) && members.length == 13 && members.all? { |member| nonempty_string?(member) }
    errors << "work topic #{index + 1} item_ids must contain exactly 13 explicit IDs"
    members = []
  end
  unless members == EXPECTED_TOPIC_ITEM_IDS
    errors << "work topic #{index + 1} item_ids must match the approved respiratory set"
  end
  errors << "work topic #{index + 1} item_ids must be unique" unless members.uniq == members
  unknown_members = members.reject { |member| item_ids.include?(member) }
  errors << "work topic #{index + 1} references non-item IDs: #{unknown_members.join(', ')}" unless unknown_members.empty?
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
  catalog = JSON.parse(File.read(catalog_path))
  catalog.each do |record|
    found = record.keys & prohibited_columns
    errors << "generated catalog contains maintenance-only fields: #{found.join(', ')}" unless found.empty?
    errors << "generated catalog schema mismatch for #{record['repository']}" unless record.keys == EXPECTED_CATALOG_COLUMNS
  end
end

catalog_csv_path = File.join(ROOT, "research-repositories.csv")
if File.exist?(catalog_csv_path)
  catalog_csv = CSV.read(catalog_csv_path, headers: true)
  errors << "generated catalog CSV schema mismatch" unless catalog_csv.headers == EXPECTED_CATALOG_COLUMNS
end

generated_work_path = File.join(ROOT, "_data/generated/work.json")
if File.exist?(generated_work_path)
  generated_work = JSON.parse(File.read(generated_work_path))
  errors << "generated work topics do not match work.yml" unless generated_work["topics"] == topics
end

homepage = items.select { |item| item.dig("selected", "homepage") }
errors << "homepage must contain 3 to 6 selected works" unless (3..6).cover?(homepage.length)

canonical_routes = Array(routes["canonical"])
unless canonical_routes == EXPECTED_CANONICAL_ROUTES
  errors << "canonical routes must be exactly: #{EXPECTED_CANONICAL_ROUTES.join(', ')}"
end
canonical_routes.each do |route|
  errors << "canonical route must begin and end with /: #{route}" unless route.start_with?("/") && route.end_with?("/")
end

expected_navigation = [
  {"title" => "About", "url" => "/"},
  {"title" => "Work", "url" => "/work/"},
  {"title" => "CV", "url" => "/cv/"}
]
unless Array(navigation["main"]) == expected_navigation
  errors << "principal navigation must be exactly About, Work, and CV"
end
redirects = Array(routes["redirects"])
errors << "redirect registry must contain exactly 31 routes" unless redirects.length == 31
redirect_sources = redirects.filter_map { |redirect| redirect["from"] }
duplicate_redirects = redirect_sources.tally.select { |_route, count| count > 1 }.keys
errors << "duplicate redirect routes: #{duplicate_redirects.join(', ')}" unless duplicate_redirects.empty?
redirects.each do |redirect|
  errors << "redirect missing from/to" unless redirect["from"] && redirect["to"]
  next unless redirect["from"] && redirect["to"]

  errors << "redirect source must begin with /: #{redirect['from']}" unless redirect["from"].start_with?("/")
  errors << "redirect source conflicts with a canonical route: #{redirect['from']}" if canonical_routes.include?(redirect["from"])
  target_route = redirect["to"].split("#", 2).first
  errors << "redirect target is not canonical: #{redirect['to']}" unless canonical_routes.include?(target_route)
end

if errors.empty?
  live_count = records.count { |record| record["live_url"] }
  puts "Site data valid: #{records.length} work records, #{homepage.length} homepage selections, #{topics.length} topic, #{live_count} live sites."
else
  warn errors.map { |error| "ERROR: #{error}" }.join("\n")
  exit 1
end
