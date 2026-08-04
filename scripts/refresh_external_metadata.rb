#!/usr/bin/env ruby
# frozen_string_literal: true

require "cgi"
require "fileutils"
require "json"
require "net/http"
require "time"
require "uri"
require "yaml"
require_relative "metadata_reconciliation"

ROOT = File.expand_path("..", __dir__)
OUTPUT = File.join(ROOT, "_data/external")
USER_AGENT = "reblocke-academic-site/1.0 (mailto:brian.locke@hsc.utah.edu)"

def request_json(url, headers = {})
  uri = URI(url)
  request = Net::HTTP::Get.new(uri)
  request["User-Agent"] = USER_AGENT
  request["Accept"] = "application/json"
  headers.each { |key, value| request[key] = value if value && !value.empty? }
  response = Net::HTTP.start(uri.host, uri.port, use_ssl: true, read_timeout: 30) { |http| http.request(request) }
  raise "#{url} returned #{response.code}" unless response.is_a?(Net::HTTPSuccess)

  [JSON.parse(response.body), response]
end

def post_form_json(url, fields)
  uri = URI(url)
  request = Net::HTTP::Post.new(uri)
  request["User-Agent"] = USER_AGENT
  request["Accept"] = "application/json"
  request.set_form_data(fields)
  response = Net::HTTP.start(uri.host, uri.port, use_ssl: true, read_timeout: 30) { |http| http.request(request) }
  raise "#{url} returned #{response.code}" unless response.is_a?(Net::HTTPSuccess)

  JSON.parse(response.body)
end

def orcid_headers
  client_id = ENV["ORCID_CLIENT_ID"]
  client_secret = ENV["ORCID_CLIENT_SECRET"]
  headers = {"Accept" => "application/vnd.orcid+json"}
  return headers if client_id.to_s.empty? || client_secret.to_s.empty?

  token = post_form_json(
    "https://orcid.org/oauth/token",
    {"client_id" => client_id, "client_secret" => client_secret, "grant_type" => "client_credentials", "scope" => "/read-public"}
  )
  headers.merge("Authorization" => "Bearer #{token.fetch('access_token')}")
end

def write_json(name, records)
  FileUtils.mkdir_p(OUTPUT)
  File.write(File.join(OUTPUT, name), MetadataReconciliation.stable_pretty_json(records) + "\n")
end

def existing_json(name)
  path = File.join(OUTPUT, name)
  File.exist?(path) ? JSON.parse(File.read(path)) : []
end

def summarize_changes(before, after, key)
  old = before.to_h { |record| [record.fetch(key), record] }
  new = after.to_h { |record| [record.fetch(key), record] }
  {
    "added" => (new.keys - old.keys).sort,
    "removed" => (old.keys - new.keys).sort,
    "changed" => (new.keys & old.keys).select { |value| new[value] != old[value] }.sort
  }
end

work = YAML.safe_load_file(File.join(ROOT, "_data/work.yml"), aliases: false)
previous_github = existing_json("github_repositories.generated.json")
previous_orcid = existing_json("orcid_works.generated.json")
previous_crossref = existing_json("crossref_works.generated.json")
previous_pubmed = existing_json("pubmed_works.generated.json")
github_headers = {"Authorization" => ENV["GITHUB_TOKEN"] && "Bearer #{ENV['GITHUB_TOKEN']}", "X-GitHub-Api-Version" => "2022-11-28"}

github_records = []
page = 1
loop do
  payload, = request_json("https://api.github.com/users/reblocke/repos?type=owner&sort=full_name&per_page=100&page=#{page}", github_headers)
  public_records = payload.select { |repo| !repo["private"] && repo.dig("owner", "login") == "reblocke" }
  github_records.concat(public_records.map do |repo|
    release = nil
    begin
      release_payload, = request_json("https://api.github.com/repos/#{repo['full_name']}/releases/latest", github_headers)
      release = release_payload["tag_name"]
    rescue RuntimeError
      release = nil
    end
    {
      "full_name" => repo["full_name"], "description" => repo["description"], "html_url" => repo["html_url"],
      "visibility" => "public",
      "archived" => repo["archived"], "fork" => repo["fork"], "topics" => Array(repo["topics"]).sort,
      "primary_language" => repo["language"], "default_branch" => repo["default_branch"],
      "latest_release" => release, "created_at" => repo["created_at"], "updated_at" => repo["updated_at"]
    }
  end)
  break if payload.length < 100
  page += 1
end
write_json("github_repositories.generated.json", github_records.sort_by { |repo| repo["full_name"].downcase })

orcid, = request_json("https://pub.orcid.org/v3.0/0000-0002-3588-5238/works", orcid_headers)
orcid_records = Array(orcid["group"]).map do |group|
  summary = Array(group["work-summary"]).first || {}
  external_ids = Array(group.dig("external-ids", "external-id")).to_h do |identifier|
    [identifier["external-id-type"], identifier["external-id-value"]]
  end
  {
    "put_code" => summary["put-code"], "title" => summary.dig("title", "title", "value"),
    "type" => summary["type"], "year" => summary.dig("publication-date", "year", "value")&.to_i,
    "doi" => external_ids["doi"] && MetadataReconciliation.normalize_doi(external_ids["doi"]), "pmid" => external_ids["pmid"],
    "url" => summary.dig("url", "value"), "last_modified" => summary.dig("last-modified-date", "value")
  }
end.sort_by { |record| [record["doi"].to_s, record["put_code"].to_i] }
write_json("orcid_works.generated.json", orcid_records)

canonical_records = Array(work["items"]) + Array(work["repositories"])
dois = (canonical_records.filter_map { |item| item["doi"] } + orcid_records.filter_map { |item| item["doi"] }).map { |doi| MetadataReconciliation.normalize_doi(doi) }.reject(&:empty?).uniq.sort
crossref_records = dois.filter_map do |doi|
  begin
    payload, = request_json("https://api.crossref.org/works/#{CGI.escape(doi)}?mailto=brian.locke@hsc.utah.edu")
    message = payload["message"]
    authors = Array(message["author"]).map { |author| [author["family"], author["given"]].compact.join(", ") }.join("; ")
    year = message.dig("published-print", "date-parts", 0, 0) || message.dig("published-online", "date-parts", 0, 0)
    {"doi" => doi, "title" => Array(message["title"]).first, "authors" => authors, "venue" => Array(message["container-title"]).first, "year" => year, "type" => message["type"], "url" => message["URL"]}
  rescue RuntimeError => e
    warn "Crossref refresh skipped #{doi}: #{e.message}"
    nil
  end
end
write_json("crossref_works.generated.json", crossref_records)

pmids = (canonical_records.filter_map { |item| item["pmid"] } + orcid_records.filter_map { |item| item["pmid"] }).map { |pmid| MetadataReconciliation.normalize_pmid(pmid) }.reject(&:empty?).uniq.sort
pubmed_records = []
unless pmids.empty?
  api_key = ENV["NCBI_API_KEY"]
  url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=#{pmids.join(',')}"
  url += "&api_key=#{CGI.escape(api_key)}" if api_key && !api_key.empty?
  payload, = request_json(url)
  Array(payload.dig("result", "uids")).each do |pmid|
    record = payload.dig("result", pmid) || {}
    doi = Array(record["articleids"]).find { |identifier| identifier["idtype"] == "doi" }&.dig("value")
    pmcid = Array(record["articleids"]).find { |identifier| identifier["idtype"] == "pmc" }&.dig("value")
    pubmed_records << {"pmid" => pmid, "pmcid" => pmcid, "doi" => doi&.downcase, "title" => record["title"], "venue" => record["fulljournalname"], "pubdate" => record["pubdate"]}
  end
end
write_json("pubmed_works.generated.json", pubmed_records.sort_by { |record| record["pmid"].to_i })

reconciliation = MetadataReconciliation.build(work: work, orcid_records: orcid_records, crossref_records: crossref_records)
write_json("reconciliation.generated.json", reconciliation)
write_json(
  "refresh_summary.generated.json",
  {
    "github" => summarize_changes(previous_github, github_records, "full_name"),
    "orcid" => summarize_changes(previous_orcid, orcid_records, "put_code"),
    "crossref" => summarize_changes(previous_crossref, crossref_records, "doi"),
    "pubmed" => summarize_changes(previous_pubmed, pubmed_records, "pmid")
  }
)
puts "Refreshed #{github_records.length} repositories, #{orcid_records.length} ORCID works, #{crossref_records.length} DOI records, and #{pubmed_records.length} PubMed records."
