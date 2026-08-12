#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "fileutils"
require "json"
require "tmpdir"
require "yaml"

ROOT = File.expand_path("..", __dir__)
GENERATED_PATHS = [
  "llms.txt",
  "research-repositories.json",
  "research-repositories.csv",
  "_data/generated/research_repositories.json",
  "_data/generated/work.json",
  "_generated_routes"
].freeze

def load_yaml(path)
  YAML.safe_load_file(File.join(ROOT, path), aliases: false) || {}
end

def load_json(path, fallback)
  full = File.join(ROOT, path)
  File.exist?(full) ? JSON.parse(File.read(full)) : fallback
end

def generate(destination)
  work = load_yaml("_data/work.yml")
  routes = load_yaml("config/routes.yml")
  github = load_json("_data/external/github_repositories.generated.json", [])
  github_by_name = github.to_h { |record| [record["full_name"], record] }

  # External metadata is reconciliation evidence, not a second editorial source.
  # Scheduled pull requests expose proposed changes for review; rendered facts
  # continue to come from work.yml until a maintainer accepts them there.
  effective_items = Array(work["items"]).map(&:dup).sort_by { |item| [item["order"] || 99_999, item["id"]] }

  effective = {"sections" => work["sections"], "items" => effective_items, "repositories" => work["repositories"]}
  write_file(destination, "_data/generated/work.json", JSON.pretty_generate(effective) + "\n")

  catalog = Array(work["repositories"]).map do |record|
    remote = github_by_name[record["repository"]] || {}
    related = effective_items.find { |item| item["id"] == record["related_id"] } || {}
    {
      "repository" => record["repository"],
      "title" => record["title"],
      "artifact_type" => record["artifact_type"],
      "analysis_language" => record["analysis_language"],
      "related_doi" => record["doi"] || related["doi"],
      "related_pmid" => record["pmid"] || related["pmid"],
      "data_availability" => record["data_availability"],
      "license_status" => record["license"],
      "public_url" => remote["html_url"] || "https://github.com/#{record['repository']}",
      "archived" => remote.fetch("archived", false),
      "default_branch" => remote["default_branch"],
      "latest_release" => remote["latest_release"]
    }
  end.sort_by { |record| record["repository"].downcase }

  json = JSON.pretty_generate(catalog) + "\n"
  write_file(destination, "research-repositories.json", json)
  write_file(destination, "_data/generated/research_repositories.json", json)

  headers = %w[repository title artifact_type analysis_language related_doi related_pmid data_availability license_status public_url archived default_branch latest_release]
  csv = CSV.generate do |out|
    out << headers
    catalog.each { |record| out << headers.map { |header| record[header] } }
  end
  write_file(destination, "research-repositories.csv", csv)

  selected = effective_items.select { |item| item.dig("selected", "work") }
  llms = [
    "# Brian W. Locke academic website",
    "",
    "> Public academic profile and curated index of scholarly work.",
    "",
    "## Principal pages",
    "",
    "- About: https://reblocke.github.io/",
    "- Biography: https://reblocke.github.io/bio/",
    "- Work: https://reblocke.github.io/work/",
    "- CV: https://reblocke.github.io/cv/",
    "- Public repository catalog: https://reblocke.github.io/research-repositories/",
    "",
    "## Selected scholarly work",
    ""
  ]
  selected.each do |item|
    url = item["doi"] ? "https://doi.org/#{item['doi']}" : "https://reblocke.github.io/work/"
    llms << "- #{item['title']} (#{item['year']}): #{url}"
  end
  llms += ["", "## Machine-readable data", "", "- https://reblocke.github.io/research-repositories.json", "- https://reblocke.github.io/research-repositories.csv", ""]
  write_file(destination, "llms.txt", llms.join("\n"))

  route_dir = File.join(destination, "_generated_routes")
  FileUtils.mkdir_p(route_dir)
  Array(routes["redirects"]).each_with_index do |redirect, index|
    body = <<~MARKDOWN
      ---
      layout: redirect
      permalink: #{redirect.fetch("from")}
      redirect_to: #{redirect.fetch("to")}
      sitemap: false
      ---
    MARKDOWN
    File.write(File.join(route_dir, format("redirect-%02d.md", index + 1)), body)
  end
end

def write_file(root, path, content)
  full = File.join(root, path)
  FileUtils.mkdir_p(File.dirname(full))
  File.write(full, content)
end

mode = ARGV.first || "--check"
if mode == "--write"
  GENERATED_PATHS.each { |path| FileUtils.rm_rf(File.join(ROOT, path)) }
  generate(ROOT)
  puts "Generated site indexes and redirects."
elsif mode == "--check"
  Dir.mktmpdir("site-generated-") do |tmp|
    generate(tmp)
    mismatches = GENERATED_PATHS.reject do |path|
      expected = File.join(tmp, path)
      actual = File.join(ROOT, path)
      if File.directory?(expected)
        expected_files = Dir.glob("**/*", base: expected).select { |entry| File.file?(File.join(expected, entry)) }
        actual_files = File.directory?(actual) ? Dir.glob("**/*", base: actual).select { |entry| File.file?(File.join(actual, entry)) } : []
        expected_files == actual_files && expected_files.all? { |entry| File.binread(File.join(expected, entry)) == File.binread(File.join(actual, entry)) }
      else
        File.exist?(actual) && File.binread(expected) == File.binread(actual)
      end
    end
    abort "Generated outputs are stale: #{mismatches.join(', ')}. Run scripts/generate_indexes.rb --write." unless mismatches.empty?
  end
  puts "Generated outputs are current."
else
  abort "Usage: scripts/generate_indexes.rb [--write|--check]"
end
